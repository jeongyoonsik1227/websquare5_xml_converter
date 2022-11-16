
# Node Type Definition
ATTRIBUTE_NODE = 2
CDATA_SECTION_NODE = 4
COMMENT_NODE = 8
DOCUMENT_FRAGMENT_NODE = 11
DOCUMENT_NODE = 9
DOCUMENT_TYPE_NODE = 10
ELEMENT_NODE = 1
ENTITY_NODE = 6
ENTITY_REFERENCE_NODE = 5
NOTATION_NODE = 12
PROCESSING_INSTRUCTION_NODE = 7
TEXT_NODE = 3

# Default screen sizee
DEFAULT_SCREEN_WIDTH = 1024

# Child node
localname_last_node_arr = ["trigger", "gridView", "select1", "select"]


# Rows 분류 기준
row_threshold = 10
# Column 분류 기준 (요소의 left 와 요소(-1) right 의 거리가 이 수치를 넘기면 서로 다른 column 으로 본다.)
col_threshold = 40
# 동일 Column 분류 기준
same_col_threshold = 30
# 최소 th 폭
least_th_width = 20
# th 최소 간격
th_threshold = 150
# tr minimum height
min_height = 20
# row height
row_height = 50
# group space (row * 20)
group_space_extra = 27
# group 간의 간격.
group_space = 50
