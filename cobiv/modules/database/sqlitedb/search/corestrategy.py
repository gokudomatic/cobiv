import time

from cobiv.modules.database.sqlitedb.search.defaultstrategy import DefaultSearchStrategy


class CoreStrategy(DefaultSearchStrategy):
    tablename = "core_tags"
    fields = ['path', 'size', 'file_date', 'ext']

    def __init__(self,**kwargs):
        super(CoreStrategy, self).__init__()

        if kwargs.has_key('tablename'):
            self.tablename=kwargs.get('tablename')
        if kwargs.has_key('file_key'):
            self.file_key_name=kwargs.get('file_key')
        if kwargs.has_key('fields'):
            self.fields=kwargs.get('fields')

        self.operator_functions = {
            'in': [self.prepare_in, self.parse_in, self.join_query_core_tags],
            '%': [self.prepare_in, self.parse_partial, self.join_query_core_tags],
            '>': [self.prepare_greater_than, self.parse_greater_than, self.join_query_core_tags],
            '<': [self.prepare_lower_than, self.parse_lower_than, self.join_query_core_tags],
            '>=': [self.prepare_greater_than, self.parse_greater_equals, self.join_query_core_tags],
            '<=': [self.prepare_lower_than, self.parse_lower_equals, self.join_query_core_tags],
            '><': [self.prepare_in, self.parse_between, self.join_query_core_tags],
            'YY': [self.prepare_in, self.parse_in_year, self.join_query_core_tags],
            'YM': [self.prepare_in, self.parse_in_year_month, self.join_query_core_tags],
            'YMD': [self.prepare_in, self.parse_in_year_month_day, self.join_query_core_tags]
        }

    def prepare(self, is_excluding, lists, kind, fn, values):
        if not lists.has_key(self.tablename):
            lists[self.tablename] = ({}, {})

        to_include, to_exclude = lists[self.tablename]
        self.prepare_function(to_exclude if is_excluding else to_include, fn, kind, values)

    def process(self, lists, subqueries):
        if not lists.has_key(self.tablename):
            return

        to_include, to_exclude = lists[self.tablename]

        subquery = ""

        if len(to_include) > 0:
            for kind in to_include:
                for fn in to_include[kind]:
                    values = to_include[kind][fn]
                    subquery += " and " * (len(subquery) > 0)
                    subquery += self.render_function(fn, kind, values, False)

        if len(to_exclude) > 0:
            for kind in to_exclude:
                for fn in to_exclude[kind]:
                    values = to_exclude[kind][fn]
                    subquery += " and " * (len(subquery) > 0)
                    subquery += "not " + self.render_function(fn, kind, values, True)

        subqueries.append((False, "select %s from %s where %s" % (self.file_key_name, self.tablename, subquery)))

    def is_managing_kind(self, kind):
        return kind in self.fields

    def prepare_in(self, crit_list, fn, kind, values):
        if not crit_list[kind].has_key(fn):
            crit_list[kind][fn] = []
        crit_list[kind][fn].append(values)

    def parse_in(self, kind, values_set):
        result = ""
        for values in values_set:
            result += self.add_query(result, " and ", '%s in ("%s")' % (kind, '", "'.join(values)))
        return result

    def parse_partial(self, kind, values_set):
        result = ""
        for value in values_set:
            result += self.add_query(result, " or ", '%s like "%s"' % (kind, value))
        return result

    def parse_greater_than(self, kind, value):
        return 'cast(%s as float)>%s' % (kind, value)

    def parse_lower_than(self, kind, value):
        return 'cast(%s as float)<%s' % (kind, value)

    def parse_greater_equals(self, kind, value):
        return 'cast(%s as float)>=%s' % (kind, value)

    def parse_lower_equals(self, kind, value):
        return 'cast(%s as float)<=%s' % (kind, value)

    def parse_between(self, kind, sets_values):
        result = ''
        for values in sets_values:
            it = iter(values)
            subquery = ''
            for val_from in it:
                val_to = it.next()
                subquery += self.add_query(subquery, ' or ',
                                           'cast(%s as float) between %s and %s' % (kind, val_from, val_to))

            result += self.add_query(result, ' and ', '(%s)' % subquery)

        return result

    def parse_in_date(self, kind, sets_values, fn_from, fn_to):
        subquery = ''
        for values in sets_values:
            for value in values:
                date_from = fn_from(value)
                date_to = fn_to(value)
                subquery += self.add_query(subquery, ' or ', 'cast(%s as float) between %s and %s' % (kind,
                                                                                                      time.mktime(
                                                                                                          date_from.timetuple()),
                                                                                                      time.mktime(
                                                                                                          date_to.timetuple())))
        return "(%s)" % subquery

    # Joins
    def join_query_core_tags(self, fn, kind, values, is_except=False):
        return fn(kind, values)

    def join_in_query_core_tags(self, fn, kind, valueset, is_except=False):
        query = ''
        joiner = ' or ' if is_except else ' and '
        for values in valueset:
            query += self.add_query(query, joiner, fn(kind, values))

        return "%s (%s)" % ("not" if is_except else "", query)

    def get_sort_query(self, kind, order, is_number):
        return kind + ' desc' * order

    def get_sort_field(self, kind, order, is_number):
        return kind

