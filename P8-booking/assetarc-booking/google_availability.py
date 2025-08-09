
import os, datetime
from dateutil import parser, tz
from google.oauth2 import service_account
from googleapiclient.discovery import build
def _svc():
    path=os.getenv('GOOGLE_SA_JSON_PATH','./google-sa.json')
    scopes=['https://www.googleapis.com/auth/calendar.readonly']
    creds=service_account.Credentials.from_service_account_file(path, scopes=scopes)
    return build('calendar','v3', credentials=creds, cache_discovery=False)
def freebusy(start_iso: str, end_iso: str, calendar_id: str):
    service=_svc()
    body={'timeMin': start_iso, 'timeMax': end_iso, 'items':[{'id':calendar_id}]}
    fb=service.freebusy().query(body=body).execute()
    busy=fb['calendars'][calendar_id]['busy']
    return busy
def business_slots(from_date: str, to_date: str, cal_id: str, tz_name: str, window: str):
    tzinfo=tz.gettz(tz_name)
    from_dt=datetime.datetime.fromisoformat(from_date).replace(tzinfo=tzinfo)
    to_dt=datetime.datetime.fromisoformat(to_date).replace(tzinfo=tzinfo)
    start_h,start_m=map(int, window.split('-')[0].split(':'))
    end_h,end_m=map(int, window.split('-')[1].split(':'))
    busy=freebusy(from_dt.isoformat(), to_dt.isoformat(), cal_id)
    slots=[]; cur=from_dt
    while cur.date()<=to_dt.date():
        day_start=cur.replace(hour=start_h, minute=start_m, second=0)
        day_end=cur.replace(hour=end_h, minute=end_m, second=0)
        t=day_start
        while t<day_end:
            t_end=t+datetime.timedelta(minutes=60)
            conf=False
            for b in busy:
                b_s=parser.isoparse(b['start']).astimezone(tzinfo)
                b_e=parser.isoparse(b['end']).astimezone(tzinfo)
                if not (t_end<=b_s or t>=b_e): conf=True; break
            if not conf: slots.append({'start':t.isoformat(),'end':t_end.isoformat()})
            t=t_end
        cur += datetime.timedelta(days=1)
    return slots
