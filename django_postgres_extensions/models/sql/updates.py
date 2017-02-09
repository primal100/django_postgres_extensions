class UpdateArrayByIndex(object):

    def __init__(self, indexes, value, field):
        self.indexes = indexes
        self.value = value
        self.base_field = field.base_field

    def alter_name(self, name, qn):
        for index in self.indexes:
            name += "[%s]" % index
        return name

