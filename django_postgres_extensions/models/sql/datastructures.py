from django.db.models.sql.datastructures import Join as BaseJoin

#class Join(BaseJoin):

def as_sql(self, compiler, connection):
    """
    Generates the full
       LEFT OUTER JOIN sometable ON sometable.somecol = othertable.othercol, params
    clause for this join.
    """
    join_conditions = []
    params = []
    qn = compiler.quote_name_unless_alias
    qn2 = connection.ops.quote_name

    # Add a join condition for each pair of joining columns.

    for index, (lhs_col, rhs_col) in enumerate(self.join_cols):
        if hasattr(self.join_field, 'get_join_on'):
            join_condition = self.join_field.get_join_on(qn(self.parent_alias), qn2(lhs_col), qn(self.table_alias),
                                                         qn2(rhs_col))
            join_conditions.append(join_condition)
        else:
            join_conditions.append('%s.%s = %s.%s' % (
                qn(self.parent_alias),
                qn2(lhs_col),
                qn(self.table_alias),
                qn2(rhs_col),
            ))

    # Add a single condition inside parentheses for whatever
    # get_extra_restriction() returns.
    extra_cond = self.join_field.get_extra_restriction(
        compiler.query.where_class, self.table_alias, self.parent_alias)
    if extra_cond:
        extra_sql, extra_params = compiler.compile(extra_cond)
        join_conditions.append('(%s)' % extra_sql)
        params.extend(extra_params)

    if not join_conditions:
        # This might be a rel on the other end of an actual declared field.
        declared_field = getattr(self.join_field, 'field', self.join_field)
        raise ValueError(
            "Join generated an empty ON clause. %s did not yield either "
            "joining columns or extra restrictions." % declared_field.__class__
        )
    on_clause_sql = ' AND '.join(join_conditions)
    alias_str = '' if self.table_alias == self.table_name else (' %s' % self.table_alias)
    sql = '%s %s%s ON (%s)' % (self.join_type, qn(self.table_name), alias_str, on_clause_sql)
    return sql, params