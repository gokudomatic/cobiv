from dateutil.relativedelta import relativedelta
import datetime, time


class SqliteFunctions(object):
    fields = {}

    def __init__(self, session, **kwargs):
        super(SqliteFunctions, self).__init__(**kwargs)

        self.session = session

        self.fields['MKDATE'] = self.mkdate
        self.fields['NOW'] = self.get_now
        self.fields['TODAY'] = self.get_today
        self.fields['ADD_DATE'] = self.add_date
        self.fields['TO_Y'] = self.get_year
        self.fields['TO_YM'] = self.get_year_month
        self.fields['TO_YMD'] = self.get_year_month_day
        self.fields['CURRENT_FILENAME'] = lambda: self.session.cursor.filename
        self.fields['CURRENT_FILEDATE'] = lambda: self.get_current_file_tag('modification_date')
        self.fields['CURRENT'] = lambda kind: self.get_current_file_tag(kind)

    def get_current_file_tag(self, category, field_name):
        if self.session.cursor.file_id is None:
            return None
        if not field_name in self.session.cursor.get_tags()[category]:
            return None

        values = self.session.cursor.get_tags()[category][field_name]
        value = values[0] if len(values) > 0 else None
        return value

    def mkdate(self, value_ymd):
        d = datetime.datetime.strptime(str(value_ymd), '%Y%m%d')
        return time.mktime(d.timetuple())

    def get_now(self):
        return time.time()

    def get_today(self):
        return time.mktime(datetime.date.today().timetuple())

    def get_year(self, ts):
        return datetime.datetime.fromtimestamp(ts).year

    def get_year_month(self, ts):
        return datetime.datetime.fromtimestamp(ts).strftime('%Y%m')

    def get_year_month_day(self, ts):
        return datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d')

    def add_date(self, ts, kind, value):
        if kind == 'D':
            diff = relativedelta(days=value)
        elif kind == 'M':
            diff = relativedelta(months=value)
        elif kind == 'Y':
            diff = relativedelta(years=value)
        return time.mktime((datetime.datetime.fromtimestamp(ts) + diff).timetuple())
