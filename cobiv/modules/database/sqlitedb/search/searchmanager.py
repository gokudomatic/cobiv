import logging

from cobiv.modules.database.sqlitedb.search.corestrategy import CoreStrategy
from cobiv.modules.database.sqlitedb.search.defaultstrategy import DefaultSearchStrategy
from cobiv.modules.database.sqlitedb.search.sqlitefunctions import SqliteFunctions
from cobiv.libs.templite import Templite

TEMP_SORT_TABLE = 'temp_sort_table'
TEMP_PRESORT_TABLE = 'temp_presort_table'

class SearchManager(object):
    logger = logging.getLogger(__name__)

    def __init__(self, session):
        super(SearchManager, self).__init__()

        self.session = session
        self.functions = SqliteFunctions(self.session)

        self.strategies = []
        self.strategies.append(CoreStrategy())
        self.strategies.append(DefaultSearchStrategy())

    def render_text(self, original_text):
        return Templite(original_text.replace("%{", "${write(").replace("}%", ")}$")).render(**self.functions.fields)

    def explode_criteria(self, criteria):
        if criteria == ":" or criteria == "::":
            return None

        is_excluding = criteria[0] == "-"
        if is_excluding:
            criteria = criteria[1:]

        criterias = criteria.split(":")
        if len(criterias) == 1:
            kind = "*"
            fn = "%" if "%" in criteria else "in"
            values = [criteria]
        elif len(criterias) == 2:
            kind = criterias[0]
            fn = "%" if "%" in criteria else "in"
            values = criterias[1:]
        else:
            kind = criterias[0]
            fn = criterias[1]
            values = criterias[2:]

        if not kind == '*' and len(values) == 1 and (values[0] == "" or values[0] == "*"):
            fn = "any"
            values = None

        return is_excluding, kind, fn, values

    def generate_search_query(self, args):

        container = {}

        for arg in args:
            formated_arg = self.render_text(arg)
            is_excluding, kind, fn, values = self.explode_criteria(formated_arg)

            for strategy in self.strategies:
                if strategy.is_managing_kind(kind):
                    strategy.prepare(is_excluding, container, kind, fn, values)
                    break

        subqueries = []
        for strategy in self.strategies:
            strategy.process(container, subqueries)

        final_subquery = ""
        for is_excluding, subquery in subqueries:
            if is_excluding and len(final_subquery) == 0:
                final_subquery = 'select id from file'

            if not is_excluding:
                if len(final_subquery) > 0:
                    final_subquery += " intersect "
                final_subquery += subquery
            else:
                final_subquery += " except " + subquery

        self.logger.debug(final_subquery)
        query = 'select f.id,f.name from file f where f.id in (' + final_subquery + ')'
        return query

    def generate_sort_query(self, fields):
        sql_fields = ["current_set.file_key"]
        sql_sort = []
        sql_tables=[("current_set","file_key")]
        checked_tablenames=set()

        for field in fields:

            order=field.startswith('-')
            kind = field[1:] if order else field

            if kind.startswith('#'):
                is_number = True
                kind = kind[1:]
            else:
                is_number = False

            if kind == '*':
                continue

            for strategy in self.strategies:
                if strategy.is_managing_kind(kind):
                    if strategy.tablename not in checked_tablenames:
                        checked_tablenames.add(strategy.tablename)
                        sql_tables.append((strategy.tablename,strategy.file_key_name))
                    sql_fields.append(strategy.get_sort_field(kind,order,is_number))
                    sql_sort.append(strategy.get_sort_query(kind,order,is_number))
                    break

        ref_table,ref_col=sql_tables[0]
        join_query=ref_table
        if len(sql_tables)>1:
            for tablename,colname in sql_tables[1:]:
                join_query+=" inner join %s on %s.%s=%s.%s" % (tablename,tablename,colname,ref_table,ref_col)

        query = 'create temporary table %s as select %s from %s' % (
            TEMP_PRESORT_TABLE, ', '.join(sql_fields),join_query)

        if len(sql_sort)>0:
            sort_query = 'create temporary table %s as select file_key from %s order by %s ' % (
                TEMP_SORT_TABLE, TEMP_PRESORT_TABLE, ','.join(sql_sort))
        else:
            sort_query = 'create temporary table %s as select file_key from %s' % (
                TEMP_SORT_TABLE, TEMP_PRESORT_TABLE)

        self.logger.debug("query : "+query)
        self.logger.debug("sort query : "+sort_query)
        return query, sort_query
