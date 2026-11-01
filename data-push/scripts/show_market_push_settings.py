"""Read the current canonical market task list; no API calls or schedule changes."""
import json
import sys

from lark_delivery.core import catalog
from lark_delivery.core.registry import adapter_for


def current():
    result=[]
    for ref in catalog.registry()['channels']:
        if not ref.startswith('market_consultant/'):
            continue
        definition=catalog.load_channel(ref)
        adapter_for(definition)
        result.append({'channel_ref':ref,'adapter':definition['adapter'],'enabled':definition['schedule']['enabled'],
            'task_name':definition['schedule']['windows_task_name'],'hours':definition['schedule']['hours'],
            'prepare_minute':definition['schedule']['prepare_minute'],'send_minute':definition['schedule']['send_minute'],
            'targets':[{'id':target['id'],'chat_id':target['chat_id'],'name':target['display_name']}
                       for target in definition['targets'] if target['enabled']],
            'first_send_at':definition['schedule']['first_send_at']})
    return result


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps({'domain':'market_consultant','task_count':len(current()),'tasks':current(),'read_only':True},ensure_ascii=False,indent=2))
