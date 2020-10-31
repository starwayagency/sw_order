from admin_auto_filters.filters import AutocompleteSelect

class TagsFilter(AutocompleteSelect):
    title = 'тег'
    field_name = 'tags'
