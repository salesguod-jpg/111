import copy, importlib.util, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch, Mock
spec=importlib.util.spec_from_file_location('collector',Path(__file__).parents[1]/'scripts/collect.py')
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
SETTINGS=json.loads((c.ROOT/'config/settings.json').read_text())
SOURCE={'name':'Test source'}
def article(title='Federal Reserve interest rate decision',link='https://example.org/a',excerpt=''):
    return {'title':title,'url':link,'excerpt':excerpt,'published':c.now()}
class PipelineTests(unittest.TestCase):
    def test_url_normalization(self):
        self.assertEqual(c.url('https://example.org/a?utm_source=x&b=1#x'),'https://example.org/a?b=1')
        with self.assertRaises(ValueError): c.url('javascript:alert(1)')
    def test_repeat_and_tracking_do_not_duplicate(self):
        events=[]; seen={}; a=article()
        c.ingest([a],SOURCE,events,seen,SETTINGS)
        c.ingest([a,dict(a,url=a['url']+'?utm_source=x')],SOURCE,events,seen,SETTINGS)
        self.assertEqual(len(events),1)
    def test_same_event_multiple_sources(self):
        events=[];seen={};a=article()
        c.ingest([a],SOURCE,events,seen,SETTINGS)
        c.ingest([dict(a,url='https://example.net/b')],{'name':'Second'},events,seen,SETTINGS)
        self.assertEqual(len(events),1);self.assertEqual(len(events[0]['sources']),2)
    def test_numeric_changes_are_distinct(self):
        self.assertFalse(c.similar('Federal Reserve raises rate 25 basis points','Federal Reserve raises rate 50 basis points'))
    def test_material_update_stable_id(self):
        events=[];seen={};a=article(excerpt='Initial facts')
        c.ingest([a],SOURCE,events,seen,SETTINGS); event_id=events[0]['id'];v=events[0]['version']
        c.ingest([dict(a,excerpt='Corrected rate decision details')],SOURCE,events,seen,SETTINGS)
        self.assertEqual(events[0]['id'],event_id);self.assertNotEqual(events[0]['version'],v);self.assertTrue(events[0]['development'])
    def test_no_key_no_calls(self):
        session=Mock()
        with patch.dict(os.environ,{},clear=True): self.assertFalse(c.analyze({}, {}, SETTINGS,session))
        session.post.assert_not_called()
    def test_bad_ai_json_and_retry_budget(self):
        events=[];c.ingest([article()],SOURCE,events,{},SETTINGS)
        session=Mock();session.post.return_value=Mock(status_code=200);session.post.return_value.json.return_value={'output':[{'content':[{'type':'output_text','text':'{broken'}]}]}
        state={}
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-not-real','OPENAI_MODEL':'test-model'}):
            for _ in range(4): self.assertFalse(c.analyze(events[0],state,SETTINGS,session))
        self.assertEqual(session.post.call_count,2);self.assertEqual(next(iter(state['usage'].values()))['failed'],2)
    def test_budget_stops_calls(self):
        settings=copy.deepcopy(SETTINGS);settings['ai']['daily_calls']=0
        events=[];c.ingest([article()],SOURCE,events,{},SETTINGS);session=Mock()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test','OPENAI_MODEL':'test'}):self.assertFalse(c.analyze(events[0],{},settings,session))
        session.post.assert_not_called()
    def test_atomic_write_and_corrupt_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.json';self.assertTrue(c.write(p,{'a':1}));self.assertFalse(c.write(p,{'a':1}));p.write_text('{bad')
            with self.assertRaises(json.JSONDecodeError):c.read(p,{})
            self.assertEqual(p.read_text(),'{bad')
    def test_feed_failure_preserves_history_and_no_content_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c.write(root/'config/settings.json',SETTINGS)
            c.write(root/'config/sources.json',[{'id':'broken','name':'broken','url':'https://example.org/rss','enabled':True,'min_interval_minutes':0,'max_age_days':30}])
            events=[];c.ingest([article()],SOURCE,events,{},SETTINGS)
            month=events[0]['published_at'][:7];c.write(root/'site/data/archive'/f'{month}.json',events)
            with patch.object(c.requests.Session,'get',side_effect=c.requests.ConnectionError),patch.dict(os.environ,{},clear=True):
                c.run(root); old=(root/'site/data/index.json').read_bytes();c.run(root)
            self.assertEqual(old,(root/'site/data/index.json').read_bytes())
            self.assertEqual(len(c.read(root/'site/data/archive'/f'{month}.json',[])),1)
            self.assertIsNone(c.read(root/'site/data/status.json',{})['last_success_at'])
    def test_conditional_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c.write(root/'config/settings.json',SETTINGS)
            c.write(root/'config/sources.json',[{'id':'f','name':'f','url':'https://example.org/rss','enabled':True,'min_interval_minutes':0,'max_age_days':30}])
            c.write(root/'state/state.json',{'seen':{},'feeds':{'f':{'etag':'abc'}},'attempts':{},'usage':{}})
            response=Mock(status_code=304)
            with patch.object(c.requests.Session,'get',return_value=response) as get,patch.dict(os.environ,{},clear=True):
                status=c.run(root)
            self.assertEqual(get.call_args.kwargs['headers']['If-None-Match'],'abc');self.assertEqual(status['sources']['f']['state'],'not_modified')
if __name__=='__main__': unittest.main()
