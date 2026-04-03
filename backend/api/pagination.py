from rest_framework.pagination import PageNumberPagination


class FlexPageNumberPagination(PageNumberPagination):
    """允許 client 端透過 ?page_size= 指定每頁筆數，上限 1000。"""
    page_size_query_param = 'page_size'
    max_page_size = 1000
