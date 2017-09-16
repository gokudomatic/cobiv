import calendar,datetime, time

from cobiv.modules.database.sqlitedb.search.abstractsearchstrategy import AbstractSearchStrategy


class DefaultSearchStrategy(AbstractSearchStrategy):

    def __init__(self):
        super(DefaultSearchStrategy, self).__init__()

        self.operator_functions = {
            'in': [self.prepare_in, self.parse_in, self.join_query_in],
            '%': [self.prepare_in, self.parse_partial, self.join_query_in],
            'any': [self.prepare_any, self.parse_any, self.join_query_default],
            '>': [self.prepare_greater_than, self.parse_greater_than, self.join_query_default],
            '<': [self.prepare_lower_than, self.parse_lower_than, self.join_query_default],
            '>=': [self.prepare_greater_than, self.parse_greater_equals, self.join_query_default],
            '<=': [self.prepare_lower_than, self.parse_lower_equals, self.join_query_default],
            '><': [self.prepare_in, self.parse_between, self.join_query_default],
            'YY': [self.prepare_in, self.parse_in_year, self.join_query_default],
            'YM': [self.prepare_in, self.parse_in_year_month, self.join_query_default],
            'YMD': [self.prepare_in, self.parse_in_year_month_day, self.join_query_default]
        }

    def is_managing_kind(self, kind):
        return True

    def process(self, lists, subqueries):
        if not lists.has_key('default'):
            return

        to_include,to_exclude = lists['default']

        if len(to_include) > 0:
            for kind in to_include:
                for fn in to_include[kind]:
                    values = to_include[kind][fn]
                    subqueries.append((False,self.render_function(fn, kind, values, False)))

        if len(to_exclude):
            for kind in to_exclude:
                for fn in to_exclude[kind]:
                    values = to_exclude[kind][fn]
                    subqueries.append((True,self.render_function(fn, kind, values, True)))


    def prepare(self, is_excluding,lists,kind,fn,values):

        if not lists.has_key('default'):
            lists['default'] = ({}, {})

        to_include,to_exclude = lists['default']

        self.prepare_function(to_exclude if is_excluding else to_include, fn, kind, values)

    def prepare_function(self, category_list, fn, kind, values):
        if self.operator_functions.has_key(fn):
            if not category_list.has_key(kind):
                category_list[kind]={}
            self.operator_functions[fn][0](category_list, fn, kind, values)

    def render_function(self, fn, kind, values, is_except):
        return self.operator_functions[fn][2](self.operator_functions[fn][1], kind, values, is_except)

    def prepare_in(self, crit_list, fn, kind, values):
        if not crit_list[kind].has_key(fn):
            crit_list[kind][fn] = []
        crit_list[kind][fn].append(values)

    def parse_in(self, kind, values_set):
        result = 'value in ("%s")' % '", "'.join(values_set)
        if not kind == "*":
            result = result + ' and kind="%s"' % kind
        return result

    def parse_partial(self, kind, values_set):
        result = ""
        for value in values_set:
            if len(result) > 0:
                result += " or "
            result += 'value like "%s"' % value
        if not kind == "*":
            result = result + ' and kind="%s"' % kind
        return result

    def prepare_any(self, crit_list, fn, kind, values):
        if not crit_list[kind].has_key(fn):
            crit_list[kind][fn] = None

    def parse_any(self, kind, values):
        return 'kind="%s"' % kind

    def prepare_greater_than(self, crit_list, fn, kind, values):
        candidate = min([float(i) for i in values])
        if not crit_list[kind].has_key(fn):
            crit_list[kind][fn] = candidate
        else:
            crit_list[kind][fn] = max(candidate, crit_list[kind][fn])

    def parse_greater_than(self, kind, value):
        return 'kind="%s" and cast(value as float)>%s' % (kind, value)

    def prepare_lower_than(self, crit_list, fn, kind, values):
        candidate = max([float(i) for i in values])
        if not crit_list[kind].has_key(fn):
            crit_list[kind][fn] = candidate
        else:
            crit_list[kind][fn] = min(candidate, crit_list[kind][fn])

    def parse_lower_than(self, kind, value):
        return 'kind="%s" and cast(value as float)<%s' % (kind, value)

    def parse_greater_equals(self, kind, value):
        return 'kind="%s" and cast(value as float)>=%s' % (kind, value)

    def parse_lower_equals(self, kind, value):
        return 'kind="%s" and cast(value as float)<=%s' % (kind, value)

    def parse_between(self, kind, sets_values):
        result = 'kind="%s"' % kind
        for values in sets_values:
            it = iter(values)
            subquery = ''
            for val_from in it:
                val_to = it.next()
                if len(subquery) > 0:
                    subquery += ' or '
                subquery += 'cast(value as float)>=%s and cast(value as integer)<=%s' % (val_from, val_to)
            result += ' and (' + subquery + ')'

        return result

    def parse_in_date(self, kind, sets_values, fn_from, fn_to):
        result = 'kind="%s"' % kind
        subquery = ''
        for values in sets_values:
            for value in values:
                date_from = fn_from(value)
                date_to = fn_to(value)
                if len(subquery) > 0:
                    subquery += ' or '
                subquery += 'cast(value as float) between %s and %s' % (
                    time.mktime(date_from.timetuple()), time.mktime(date_to.timetuple()))
        return result + " and (%s)" % subquery

    def parse_in_year(self, kind, sets_values):
        return self.parse_in_date(kind, sets_values, lambda d: datetime.date(int(d), 1, 1),
                                  lambda d: datetime.date(int(d), 12, 31))

    def parse_in_year_month(self, kind, sets_values):
        def fn_to(d):
            year = int(d[:4])
            month = int(d[4:])
            day_of_week, count = calendar.monthrange(year, month)
            return datetime.date(year, month, count)

        return self.parse_in_date(kind, sets_values, lambda d: datetime.date(int(d[:4]), int(d[4:]), 1), fn_to)

    def parse_in_year_month_day(self, kind, sets_values):
        return self.parse_in_date(kind, sets_values, lambda d: datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])),
                                  lambda d: datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])) + datetime.timedelta(
                                      days=1))

    # Joins

    def join_query_default(self, fn, kind, values, is_except=False):
        return "select file_key from tag where " + fn(kind, values)

    def join_query_in(self, fn, kind, valueset, is_except=False):
        query = ''
        joiner = ' except ' if is_except else ' intersect '
        for values in valueset:
            query += joiner * (len(query) > 0)
            query += "select file_key from tag where " + fn(kind, values)
        return query
