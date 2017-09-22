class AbstractSearchStrategy(object):
    """Interface for search strategy implementations.

    """
    tablename = None
    """Name of the SQL table"""
    file_key_name = "file_key"
    """Name of the column containing the file key"""

    def is_managing_kind(self, kind):
        """Tells if the strategy takes case of such kind.

        :param kind: kind to check.
        :return: True if the strategy handle such kind, or False
        """
        return False

    def prepare(self, is_excluding, lists, kind, fn, values):
        """First step of the SQL query generation.
        It parses the values by function and store them in the lists for the second step. The structure of the stored
        data is up to the strategy. The only restriction is that the data goes in one slot of the mapped list.

        :param is_excluding: True if the criteria is an exclusion rather than an inclusion.
        :param lists: mapped list of temporary data to fill, used later for the next step.
        :param kind: kind of tag to search.
        :param fn: comparator function.
        :param values: criteria to parse
        """
        pass

    def process(self, lists, subqueries):
        """Second step of the SQL query generation.
        It takes what was prepared in the first step and it generates SQL subqueries that the main search manager will
        combine with intersect or except.

        :param lists: mapped list of temporary data filled in step 1.
        :param subqueries: List of SQL subqueries to fill.
        """
        pass

    def get_sort_field(self, kind, order, is_number):
        """In the context of the sorting SQL generation, this method generates SQL code of the columns to add in the
        first temporary table.

        :param kind: kind criteria.
        :param order: True if descending, False if ascending.
        :param is_number: if True force cast float type on kind criteria.
        :return: SQL code of the column to add.
        """
        pass

    def get_sort_query(self, kind, order, is_number):
        """In the context of the sort SQL generation, this method generate SQL code of the ORDER BY part for the creation
        of the sorted secondary table.

        :param kind: kind criteria
        :param order: True if descending, False if ascending.
        :param is_number: if True force cast float type on kind criteria.
        :return: SQL code of the sorting part
        """
        pass

    @staticmethod
    def add_query(query, joiner, item):
        return (joiner * (len(query) > 0)) + item
