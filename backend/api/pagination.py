from rest_framework.pagination import PageNumberPagination


class RecipesPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = "limit"
