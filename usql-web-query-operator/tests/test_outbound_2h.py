from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import sys,unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from _shared.errors import UsageError
from read_dashboard.commands import outbound_2h as module
from read_dashboard.dashboard_change import canonical_sha256
from read_dashboard.pivot_ratio_fields import replace_ratio_fields
from read_dashboard.write_capabilities import load_capability_registry,capability_by_operation


def selection():
    return {'domain':'market_consultant','dashboard_id':module.BOARD,'dashboard_name':'外呼过程数据看板',
      'owner':'lvshuai01','model_id':2054,'subject_id':207787,'component_id':module.COMPONENT,
      'unit_id':module.UNIT,'unit_name':'总体数据','denominator':deepcopy(module.DENOMINATOR),
      'ratios':[{'name':'2h外呼','numerator':{'field_id':'123456','field_name':'first_call_in_2h'}}],
      'remove_ids':[],'move_to_end_ids':[],'anchor_id':module.ANCHOR,'header_color':None,'decimals':1}


def unit():
    fmt={'measureType':'main','dataType':1,'numberType':2,'isAggregation':False,'changeParamType':4,
      'orgParamType':4,'filterType':['aggregationFilter'],
      'columnVisualStyle':{'header':{'bgColor':'#dcefd5','color':'#000'},'body':{'color':'#000'}}}
    fields=[{'fieldId':module.DENOMINATOR['field_id'],'showName':'退后线索','format':{'dataType':1}},
      {'fieldId':module.ANCHOR,'showName':'5min外呼','fieldType':1,'frontRender':0,'format':deepcopy(fmt)}]
    for label,(field_id,_) in module.TIMELY_FIELDS.items():
        fields.append({'fieldId':field_id,'showName':label,'fieldType':1,'frontRender':0,'format':deepcopy(fmt)})
    return {'unitMeasureList':fields,'unitDimensionList':[{'fieldId':'322380'}],
      'format':{'fieldMeasureNameSortList':[f['showName'] for f in fields]}}


class Outbound2hTests(unittest.TestCase):
    def test_exact_selection_rejects_cross_scope_and_other_metric_changes(self):
        good=selection();module.validate_selection(good)
        for key,value in [('dashboard_id','dashboard_1'),('model_id',2293),('subject_id',1),
                          ('owner','dingxi01'),('unit_id','unit_1'),('domain','qingcheng'),
                          ('anchor_id',module.TEMPLATE),('remove_ids',[module.TEMPLATE]),('decimals',2)]:
            bad={**good,key:value}
            with self.subTest(key=key),self.assertRaises(UsageError):module.validate_selection(bad)
        bad=deepcopy(good);bad['denominator']['field_name']='lead_count'
        with self.assertRaises(UsageError):module.validate_selection(bad)
        bad=deepcopy(good);bad['ratios'][0]['numerator']['field_name']='first_call_in_6h'
        with self.assertRaises(UsageError):module.validate_selection(bad)

    def test_projection_adds_one_column_and_preserves_every_old_field(self):
        before=unit();s=selection();template=before['unitMeasureList'][2]
        after=replace_ratio_fields(before,s,['customized_123'],template,preserve_template_style=True)
        self.assertEqual([f['showName'] for f in after['unitMeasureList']],
                         ['退后线索','5min外呼','2h外呼','6h外呼','12h外呼','24h外呼'])
        self.assertEqual([f for f in after['unitMeasureList'] if f['fieldId']!='customized_123'],before['unitMeasureList'])
        self.assertEqual(after['unitDimensionList'],before['unitDimensionList'])
        self.assertEqual(after['unitMeasureList'][2]['format']['numberType'],2)
        self.assertEqual(after['unitMeasureList'][2]['format']['decimalPlaces'],1)
        self.assertEqual(after['unitMeasureList'][2]['format']['columnVisualStyle']['header']['bgColor'],'#dcefd5')
        template['format'].pop('columnVisualStyle')
        plain=replace_ratio_fields(before,s,['customized_123'],template,preserve_template_style=True)
        self.assertNotIn('columnVisualStyle',plain['unitMeasureList'][2]['format'])

    def test_denominator_checks_all_three_existing_formulas(self):
        def formula(_,field_id):
            numerator=next(n for i,n in module.TIMELY_FIELDS.values() if i==field_id)
            return {'subjectId':207787,'formula':f'ifnull(sum(${{{numerator}}})/sum(${{valid_lead_count}}),0)',
              'dependencyIndicators':[{'paramId':module.DENOMINATOR['field_id'],'orgParamType':1}]}
        with patch.object(module,'_formula_item',side_effect=formula):
            self.assertEqual(len(module.denominator_proof(None,unit(),207787)),3)
        def wrong(page,field_id):
            value=formula(page,field_id)
            if field_id==module.TIMELY_FIELDS['24h外呼'][0]:value['formula']=value['formula'].replace('valid_lead_count','lead_count')
            return value
        with patch.object(module,'_formula_item',side_effect=wrong),self.assertRaisesRegex(UsageError,'denominator'):
            module.denominator_proof(None,unit(),207787)

    def test_invalid_plan_and_missing_confirmation_stop_before_browser(self):
        doc={'artifact_type':module.PLAN_TYPE,'operation':module.OPERATION,'sandbox':False,
          'selection':selection(),'checks':[{'label':'total','row':[],'filters':[],'denominator':10,'numerators':[2]}]}
        doc['plan_sha256']=canonical_sha256(doc)
        with TemporaryDirectory() as temp:
            args=SimpleNamespace(domain='market_consultant',mode='apply',plan_sha256='0'*64,
              confirm_production_write=False,state_path=Path(temp)/'state.json',output=Path(temp)/'out.json')
            with patch.object(module,'import_playwright') as browser:
                with self.assertRaisesRegex(UsageError,'exact reviewed'):module.preflight(args,doc)
                args.plan_sha256=doc['plan_sha256']
                with self.assertRaisesRegex(UsageError,'confirmation'):module.preflight(args,doc)
                browser.assert_not_called()

    def test_existing_output_is_never_overwritten(self):
        with TemporaryDirectory() as temp:
            output=Path(temp)/'receipt.json'
            output.write_text('{"keep":true}',encoding='utf-8')
            args=SimpleNamespace(output=output)
            with self.assertRaisesRegex(UsageError,'refusing to overwrite'):
                module.preflight(args,{})
            self.assertEqual(output.read_text(encoding='utf-8'),'{"keep":true}')

    def test_generic_ratio_operation_stays_sandbox_only(self):
        registry=load_capability_registry()
        generic=capability_by_operation(registry,'configure_pivot_ratio_fields_draft')
        self.assertEqual(generic['write_policy'],'sandbox_only')
        dedicated=capability_by_operation(registry,module.OPERATION)
        self.assertEqual(dedicated['adapter'],module.ADAPTER)
        self.assertEqual(dedicated['write_policy'],'allowlisted')

if __name__=='__main__':unittest.main()
