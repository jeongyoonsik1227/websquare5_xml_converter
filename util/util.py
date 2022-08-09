# -*- coding: utf-8 -*-
import os
import xml
from datetime import datetime
import logging
import glob
from xml.dom.minidom import parse
from . import config


'''
    element의 left, top, width, height 정보 보관
'''


class WqElement():
    def __init__(self, element=None):
        # element
        self.element = element
        # next element
        self.next_element = None

        # Member variables
        self.class_str = ""
        self.id = ""
        self.control_id = ""

        # left
        self.left = 0
        # top
        self.top = 0
        # width
        self.width = 0
        # height
        self.height = 0
        # display
        self.display = ""
        # visibility
        self.visibility = ""
        # dataType
        self.dataType = ""

        # ETC
        self.tagName = ""
        self.localName = ""
        self.col_type = ""
        self.col_members = []
        self.right = 0
        self.bottom = 0
        self.siblings = None
        self.th_td_cnt = 0
        self.group_tr = None
        self.th_td_list = []


"""
    EqElement 생성
"""


def getEqElement(elem):
    # Get attributes and style
    attributes_and_style_map = getElementAttributesAndStyle(elem)

    # Wq Element
    wq_element = WqElement(elem)

    # Style
    wq_element.left = attributes_and_style_map["left"]
    wq_element.top = attributes_and_style_map["top"]
    wq_element.width = attributes_and_style_map["width"]
    wq_element.height = attributes_and_style_map["height"]
    wq_element.display = attributes_and_style_map["display"]
    wq_element.visibility = attributes_and_style_map["visibility"]

    # Attributes
    wq_element.id = attributes_and_style_map["id"]
    wq_element.control_id = attributes_and_style_map["control_id"]
    wq_element.class_str = attributes_and_style_map["class"]
    wq_element.dataType = attributes_and_style_map["dataType"]

    # ETC
    wq_element.tagName = elem.tagName
    wq_element.localName = elem.localName
    wq_element.right = int(wq_element.left) + int(wq_element.width)
    wq_element.bottom = int(wq_element.top) + int(wq_element.height)

    return wq_element


"""
    Get Element Attributes and Style
"""


def getElementAttributesAndStyle(elem):
    # Get attributes map
    attributes_map = get_attributes(elem)

    # Get element style
    style_map = get_element_style(elem)

    return dict(attributes_map, **style_map)


"""
    Get Element Style
"""


def get_element_style(elem):
    # Attributes 요소
    style_str = ""

    # Style 요소
    i_left = 0
    i_top = 0
    i_width = 0
    i_height = 0
    s_display = ""
    s_visibility = ""

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

    # Style 정보가 존재하는 경우만 실행.
    if len(style_str) > 0:

        # Style 추출
        style_arr = style_str.split(";")

        for style_elem in style_arr:
            if len(style_elem.strip()) == 0:
                continue

            # Element split (['width', '942px'])
            s_elem_arr = style_elem.strip().split(":")
            # style_name ('width')
            style_name = s_elem_arr[0]

            if style_name == "left":
                i_left = int(s_elem_arr[1].replace("px", ""))
            if style_name == "top":
                i_top = int(s_elem_arr[1].replace("px", ""))
            if style_name == "width":
                i_width = int(s_elem_arr[1].replace("px", ""))
            if style_name == "height":
                i_height = int(s_elem_arr[1].replace("px", ""))
            if style_name == "display":
                s_display = s_elem_arr[1].strip()
            if style_name == "visibility":
                s_visibility = s_elem_arr[1].strip()

    style_map = {"left": i_left, "top": i_top, "width": i_width, "height": i_height, "display": s_display,
                 "visibility": s_visibility}

    return style_map


"""
    부모 객체에 대해서.
    left, top 좌표로 객체를 정렬한다.
"""


def re_arrange_elements(elem):
    # Parent Node 판단.
    if len(elem.childNodes) > 0:

        wq_elem_list = []

        # minidom childnodes loop
        for e in list(elem.childNodes):

            # 기존 삭제
            elem.removeChild(e)

            # Element Node 만 추가
            if e.nodeType == config.ELEMENT_NODE:
                # EqElement를 만든다.
                wq_elem_list.append(getEqElement(e))

        # Style 정보로 기반으로 업데이트 한다.
        wq_elem_list.sort(key=lambda x: (x.top, x.left))

        # Element 목록 추가.
        for wq_e in wq_elem_list:
            elem.appendChild(wq_e.element)


"""
    attributes 를 map 으로 return
"""


def get_attributes(elem):
    id_str = ""
    control_id_str = ""
    style_str = ""
    class_str = ""
    dataType_str = ""

    # attributes 세팅.
    if elem.attributes:
        if elem.attributes.get("class"):
            class_str = elem.attributes.get("class").value
        if elem.attributes.get("id"):
            id_str = elem.attributes.get("id").value
        if elem.attributes.get("control_id"):
            control_id_str = elem.attributes.get("control_id").value
        if elem.attributes.get("style"):
            style_str = elem.attributes.get("style").value
        if elem.attributes.get("dataType"):
            dataType_str = elem.attributes.get("dataType").value

    attributes_map = {"class": class_str, "id": id_str, "control_id": control_id_str, "style": style_str,
                      "dataType": dataType_str}

    return attributes_map


"""
    minidom parser 에서 생성된 공백 Node 제거.
"""


def search_and_remove_space(node):
    if len(node.childNodes) > 0:
        child_list = list(node.childNodes)
        for c in child_list:
            # 공백 제거
            if c.nodeType == config.TEXT_NODE and c.data.isspace():
                node.removeChild(c)
            # Child 목록 조회
            search_and_remove_space(c)


"""
    group 에 속하지 않은 element 를 찾아, 적절한 group 에 포함시켜
    절대좌표에서 상대좌표 변환시 용이하게 한다.
"""


def search_relocate_nodes(p_node, xf_group_list):
    # 부모 노드이면.
    if len(p_node.childNodes) > 0:

        # EqElement를 만든다.
        p_elem = getEqElement(p_node)

        # child node loop
        for c in list(p_node.childNodes):

            # EqElement를 만든다.
            c_elem = getEqElement(c)

            # xf:group 제외
            if c.nodeName == "xf:group":
                continue

            # 재배치 실행
            # Parent 가 body 이거나
            # Self(자신)은 w2:group 이 아니고
            # Parent 의 width * height 가 0 이면.
            if p_node.tagName == "body" \
                    or (p_node.tagName == "xf:group" and p_elem.width * p_elem.height == 0):

                # group 목록 loop
                for group in xf_group_list:
                    g_left, g_top, g_width, g_height = group.left, group.top, group.width, group.height
                    c_left, c_top = c_elem.left, c_elem.top

                    # element 절대좌표 top, left 에 해당하는 group 을 찾는다.
                    if g_left <= c_left <= (g_left + g_width) \
                            and g_top <= c_top <= (g_top + g_height):
                        # 기존 부모/자식 관계를 끊는다.
                        c.parentNode.removeChild(c)

                        # 좌표에 해당하는 group 에 추가한다.
                        group.element.appendChild(c)

                        # group re_arrange by left and top
                        re_arrange_elements(group.element)

                        # Element 의 Style 을 업데이트 한다.
                        updateStyle(c_elem, group)

            # Child 목록 조회
            search_relocate_nodes(c, xf_group_list)


"""
    group table 에 attributes 와 summary 를 추가한다.
"""


def add_attributes_and_summary(document, group_table):

    # group table 에 attributes 를 추가한다.
    add_group_table_attributes(group_table)

    # Table attributes & summary
    tab_attr = document.createElement("w2:attributes")
    attr_summary = document.createElement("w2:summary")
    tab_attr.appendChild(attr_summary)

    # Table attribute/summary 추가
    group_table.element.appendChild(tab_attr)


"""
    group table 에 attributes 를 추가한다.
"""


def add_group_table_attributes(group_table):
    # Table tagname, class 세팅
    group_table.element.setAttribute("tagname", "table")
    group_table.element.setAttribute("class", "w2tb tb")


"""
    range_list 를 기준으로 각 column 별 max width 를 구한다. 0 이면 continue.
"""


def get_max_width_of_th_column(i_index, c_elem_row_list, range_list):

    # 동일 column 의 max_width
    max_width = 0

    # th 목록 구성.
    th_list = []
    for row in c_elem_row_list:
        th_list += [c for c in row if c.col_type == "th"]

    # column index 를 받아 해당 column 에서 max width 를 찾는다.
    if i_index < len(range_list):
        i_range = range_list[i_index]

        # 범위에 해당하는 th 또는 td 를 가져온다.
        th_list_0 = [c for c in th_list if i_range[0] <= c.left < i_range[1]]
        # i_index 에 해당하는 column 의 max_width 를 구한다.
        if len(th_list_0) > 0:
            max_width = max(c.width for c in th_list_0)

        # TODO : 삭제
        """
        # range_list 범위가 0~200px 라고 할 때, 시작이 0 인 경우 i_range[1] 값을
        # column 의 width 로 사용.
        # 시작이 0 이면 비어 있는 column 이므로.
        if i_index == 0 and i_range[0] == 0:
            max_width = i_range[1]
        """

    return max_width


"""
    group table 에 colgroup 을 구성하고 추가한다.
    th 의 경우 각 column 별 max_width 를 찾는다.
"""


def add_group_colgroup(document, group_table, c_elem_row_list, range_list):

    th_td_cnt_max = 0
    if len(c_elem_row_list) > 0:
        # th, td max column count
        th_td_cnt_max = max(r[0].th_td_cnt for r in c_elem_row_list)

    # colgroup 구성
    group_colgroup = document.createElement("xf:group")
    group_colgroup.setAttribute("tagname", "colgroup")
    # colgroup / col 구성
    for i_index in range(th_td_cnt_max):
        xf_group = document.createElement("xf:group")
        xf_group.setAttribute("tagname", "col")

        # range_list 를 기준으로 각 column 별 max width 를 구한다. 0 이면 continue.
        # max_width 가 0 보다 크면 width style 추가
        max_width = get_max_width_of_th_column(i_index, c_elem_row_list, range_list)
        if max_width > 0:
            xf_group.setAttribute("style", "width:{}px;".format((max_width + 20)))

        group_colgroup.appendChild(xf_group)
    # colgroup 추가
    group_table.element.appendChild(group_colgroup)


"""
    Make left min list
"""


def make_left_min_list(c_elem_row_list):

    th_list = []
    for ii, row in enumerate(c_elem_row_list):
        th_list += [c for c in row if c.col_type == "th"]

    td_list = []
    for ii, row in enumerate(c_elem_row_list):
        td_list += [c for c in row if c.col_type == "td"]

    # left 로 정렬
    th_list.sort(key=lambda x: x.left)
    td_list.sort(key=lambda x: x.left)

    # th left 목록
    th_left_list = [c.left for c in th_list]
    th_col_breaks = [i for i, (a, b) in enumerate(zip(th_left_list, th_left_list[1:]), 1) if b - a > config.th_threshold]
    th_col_groups = [th_left_list[s:e] for s, e in zip([0] + th_col_breaks, th_col_breaks + [None])]

    # td left 목록
    td_left_list = [c.left for c in td_list]
    td_col_breaks = [i for i, (a, b) in enumerate(zip(td_left_list, td_left_list[1:]), 1) if b - a > config.th_threshold]
    td_col_groups = [td_left_list[s:e] for s, e in zip([0] + td_col_breaks, td_col_breaks + [None])]

    th_td_left_min_list = []

    # th left min 목록
    if len(th_col_groups) > 0 and len(th_col_groups[0]) > 0:
        th_td_left_min_list += [min(c) for c in th_col_groups]

    # td left min 목록
    if len(td_col_groups) > 0 and len(td_col_groups[0]):
        th_td_left_min_list += [min(c) for c in td_col_groups]

    return sorted(th_td_left_min_list, key=lambda x: x)


"""
    각 column 별 left, right 범위 목록을 만든다.
"""


def make_range_list(th_td_left_list, group_table):

    # column 별 범위를 지정하기 위한 목록
    range_list = []
    for ii, c in enumerate(th_td_left_list):

        # 첫번째 range 가 떨어져 있을 경우(range > 200 px). column 을 추가한다.
        if ii == 0 and c > 200:
            range_list.append((0, c))

        if c == th_td_left_list[-1]:
            range_list.append((th_td_left_list[ii], group_table.width))
            break

        range_list.append((th_td_left_list[ii], th_td_left_list[ii + 1]))

    return range_list


"""
    빈 공간을 td 로 채워 넣는다.
"""
def fill_extra_td(document, c_elem_row_list):
    th_td_cnt_max = 0
    if len(c_elem_row_list) > 0:
        # td 빠진 부분 채워넣기.
        th_td_cnt_max = max(r[0].th_td_cnt for r in c_elem_row_list)
    for row in c_elem_row_list:
        # th_td_cnt 가 작은 경우 td 를 추가한다.
        if th_td_cnt_max > row[0].th_td_cnt:
            # loop_cnt = th_td_cnt_max - row[0].th_td_cnt
            for kk in range(th_td_cnt_max - row[0].th_td_cnt):
                # add 'td' element
                group_td = add_element_by_tag(document, "td")
                row[0].group_tr.appendChild(group_td)
                # th, td count
                row[0].th_td_cnt += 1


"""
    group_th 와 group_td 를 생성하고 c_elem_row_list 의 row[0] 에 목록 저장.
"""


def make_group_th_td_and_save_list(document, c_elem_row_list, range_list):

    # Table row 구성
    for row in c_elem_row_list:

        """
        # group row 생성
        group_tr = document.createElement("xf:group")
        group_tr.setAttribute("tagname", "tr")
        group_table.element.appendChild(group_tr)

        # group_tr 세팅
        row[0].group_tr = group_tr
        """

        # th, td count
        th_td_cnt = 0

        for kk, from_to in enumerate(range_list):

            # 범위에 해당하는 th 또는 td 를 가져온다.
            th_td_list = [c for c in row if c.col_type in ["th", "td"] and from_to[0] <= c.left < from_to[1]]

            for c in th_td_list:

                if c.col_type == "th":

                    # add 'th' element
                    group_th = add_element_by_tag(document, "th")
                    # child 추가
                    group_th.appendChild(c.element)

                    """
                    # group_tr 에 추가
                    group_tr.appendChild(group_th)
                    """

                    # wq element 의 position 정보를 삭제한다.
                    removePositionInfo(c)

                    # th_td_list 에 추가
                    row[0].th_td_list.append(group_th)

                    # th, td count
                    th_td_cnt += 1

                elif c.col_type == "td":

                    # add 'td' element
                    group_td = add_element_by_tag(document, "td")
                    # child 추가
                    for col_mem in c.col_members:
                        # 빈 td 를 tr 에 추가
                        group_td.appendChild(col_mem.element)

                        # wq element 의 position 정보를 삭제한다.
                        removePositionInfo(col_mem)

                    """
                    # group_tr 에 추가
                    group_tr.appendChild(group_td)
                    """

                    # th_td_list 에 추가
                    row[0].th_td_list.append(group_td)

                    # th, td count
                    th_td_cnt += 1

            if len(th_td_list) == 0:
                # add 'td' element
                group_td = add_element_by_tag(document, "td")

                """
                # group_tr 에 추가
                group_tr.appendChild(group_td)
                """

                # th_td_list 에 추가
                row[0].th_td_list.append(group_td)

                # th, td count
                th_td_cnt += 1

        # th_td_cnt 세팅.
        row[0].th_td_cnt = th_td_cnt


"""
    make_group_th_td_and_save_list 함수에서 저장한 th_td_list 로 group_tr 생성.
    정확한 column 개수를 확인 후 colgroup 을 완성하기 위해 로직 수정.
"""


def make_group_tr(document, group_table, c_elem_row_list):

    # Table row 구성
    for row in c_elem_row_list:

        # group row 생성
        group_tr = document.createElement("xf:group")
        group_tr.setAttribute("tagname", "tr")
        group_table.element.appendChild(group_tr)

        # group_tr 세팅
        row[0].group_tr = group_tr

        # group_tr 에 th, td 컬럼 추가
        for th_td in row[0].th_td_list:
            # group_tr 에 추가
            group_tr.appendChild(th_td)


"""
    group table 을 구성한다.
"""


def make_group_table(document, group_table, c_elem_row_list):

    # th td left 목록을 구성한다.
    th_td_left_list = make_left_min_list(c_elem_row_list)

    # 컬럼 별 좌표 범위 목록을 구성한다.
    range_list = make_range_list(th_td_left_list, group_table)

    # group_th 와 group_td 를 생성하고 c_elem_row_list 의 row[0] 에 목록 저장.
    make_group_th_td_and_save_list(document, c_elem_row_list, range_list)

    # colgroup 구성
    add_group_colgroup(document, group_table, c_elem_row_list, range_list)

    # 정확한 column 개수를 확인 후 colgroup 을 완성하기 위해 로직 수정.
    make_group_tr(document, group_table, c_elem_row_list)

    # 빈 공간을 td 로 채워 넣는다.
    fill_extra_td(document, c_elem_row_list)


"""
    th, td node 를 정의한다.
"""


def define_th_td_node(c_elem_row_list):

    # th, td 정의
    for ii, row in enumerate(c_elem_row_list):

        c_tmp = None
        hidden_list = []

        for jj, c in enumerate(row):

            # 자식 node 가 없는 group 제외
            if c.localName == "group" and len(c.element.childNodes) == 0:
                continue

            # row 에 textbox 가 없으면.
            # 그리고 첫번째이면.
            if len([x for x in row if x.localName == "textbox"]) == 0 and jj == 0:
                c.col_type = "td"
                c.col_members.append(c)
                c_tmp = c

            # textbox 다음 항목이 hidden 인 경우.
            elif len(hidden_list) > 0:
                if c.display != "none" \
                        and c.visibility != "hidden":
                    c.col_type = "td"
                    c.col_members.append(c)
                    c.col_members += hidden_list
                    c_tmp = c
                    hidden_list = []
                else:
                    hidden_list.append(c)

            # th 최소폭 보다 크면서 textbox 이면.
            elif c.display != "none" \
                    and c.visibility != "hidden" \
                    and c.localName == "textbox" \
                    and c.width > config.least_th_width:
                c.col_type = "th"
                c.col_members.append(c)
                c_tmp = c

            # 이전 member 가 th 이면.
            elif c.display != "none" \
                    and c.visibility != "hidden" \
                    and row[jj - 1].col_type == "th":
                c.col_type = "td"
                c.col_members.append(c)
                c_tmp = c

            # hidden 이고 이전이 th 이면.
            elif (c.display == "none" \
                  or c.visibility == "hidden") \
                    and row[jj - 1].col_type == "th":
                hidden_list.append(c)

            # (i-1).right 와 left 차이가 '30px' 보다 크면(벌어져 있으면).
            else:
                if c.display != "none" \
                        and c.visibility != "hidden" \
                        and row[jj - 1].right + config.same_col_threshold < c.left:

                    c.col_type = "td"
                    c.col_members.append(c)
                    c_tmp = c

                else:

                    # row 에 textbox 가 없는 경우.
                    if c_tmp is None:
                        c.col_type = "td"
                        c.col_members.append(c)
                        c_tmp = c
                    else:
                        c_tmp.col_members.append(c)


"""
    Style 에서 top 정보 를 갱신한다.
"""


def updateTop(wq_elem, i_top):
    # 원본 element
    elem = wq_elem.element

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

        # Style 추출
        style_arr = style_str.split(";")

        for i, style_elem in enumerate(style_arr):
            if len(style_elem.strip()) == 0:
                continue

            # style 에서 top 정보를 수정한다.
            if "top" in style_elem:
                style_arr.remove(style_elem)
                style_arr.insert(i, "top:{}px".format(i_top))
                break

        # Style 업데이트
        elem.attributes["style"] = ";".join(style_arr)

        # Wq element top 업데이트
        elem.top = i_top


"""
    Style 에서 height 를 갱신한다.
"""


def updateHeight(wq_elem, i_height):
    # 원본 element
    elem = wq_elem.element

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

        # Style 추출
        style_arr = style_str.split(";")

        for i, style_elem in enumerate(style_arr):
            if len(style_elem.strip()) == 0:
                continue

            # style 에서 height 정보를 수정한다.
            if "height" in style_elem:
                style_arr.remove(style_elem)
                style_arr.insert(i, "height:{}px".format(i_height))
                break

        # Style 업데이트
        elem.attributes["style"] = ";".join(style_arr)

        # Wq element height 업데이트
        elem.height = i_height

"""
    copy group_table
"""


def copy_group_table(document, group_table, i_index):
    elem = group_table.element

    # Style 수정
    # top, height 수정
    group_table_tmp = document.createElement("xf:group")

    # attributes 가 존재하면.
    # control_id
    if elem.attributes and elem.attributes.get("control_id"):
        control_id_str = elem.attributes.get("control_id").value.strip()
        group_table_tmp.setAttribute("control_id", "{}_{}".format(control_id_str, i_index))
    # id
    if elem.attributes and elem.attributes.get("id"):
        id_str = elem.attributes.get("id").value.strip()
        group_table_tmp.setAttribute("id", "{}_{}".format(id_str, i_index))
    # style
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()
        group_table_tmp.setAttribute("style", style_str)

    # 자식 Node 로서 추가
    elem.parentNode.appendChild(group_table_tmp)

    return getEqElement(group_table_tmp)


"""
    group 내에 존재하는 gridView, trigger 를 별도의 group 으로 분리하는 기능.
"""


def seperate_rows_by_grid_and_trigger(c_elem_row_list):

    # 전체 row.
    all_rows = []
    # tmp 개별 row.
    group_row_tmp = []

    for i, row in enumerate(c_elem_row_list):

        # 1. gridView 가 존재하거나.
        # 2. row 가 trigger 로만 이루어져 있는 경우.
        if len([c for c in row if c.localName == "gridView" and c.display != "none"]) > 0 \
                or len([c for c in row if c.localName == "trigger"]) == len(row):

            # group_row_tmp 를 저장 후 비워준다.
            if len(group_row_tmp) > 0:
                all_rows.append(group_row_tmp)
                group_row_tmp = []

            # all_rows 에 행 추가.
            group_row_tmp.append(row)
            all_rows.append(group_row_tmp)
            group_row_tmp = []
            continue
        
        # tmp row 추가
        group_row_tmp.append(row)

    # all_rows 에 추가되지 않은 row 가 존재하는 경우.
    if len(group_row_tmp) > 0:
        all_rows.append(group_row_tmp)

    return all_rows


"""
    최신 group_table 을 가져온다.
"""


def get_latest_group_table(body_root, group_table):

    ret_group_table = None

    # 최신 group_table 을 가져온다.
    xf_group_list = get_xf_group_list(body_root)
    for g in xf_group_list:
        if g.control_id == group_table.control_id:
            ret_group_table = g
            break

    return ret_group_table

"""
    Group 업데이트
"""


def search_and_regroup_nodes(document):
    # body Element 조회
    body_root = document.getElementsByTagName("body")[0]

    # xf:group Element 조회
    xf_group_list = get_xf_group_list(body_root)

    # Group 재구성 실횅. (재귀 실행)
    search_relocate_nodes(body_root, xf_group_list)

    # group list loop
    for group_table in xf_group_list:

        c_elem_row_list = []
        c_elem_left_min = []

        # group 이면서 width 가 700px 이상.
        # textbox 가 하나 이상.
        # if group_table.width > 700 and len([c for c in group_table.element.childNodes if c.localName == "textbox"]) > 0:
        if group_table.width > 700:

            # 최신 group_table 을 가져온다.
            group_table = get_latest_group_table(body_root, group_table)

            # Group element 의 wq element child list 를 만든다.
            c_elem_list = [getEqElement(c) for c in group_table.element.childNodes]

            # 자식 node 모두 삭제
            for c in list(group_table.element.childNodes):
                group_table.element.removeChild(c)

            # TODO : 삭제 ---------------------------------------------------------
            # if group_table.control_id == "27":
            #     print()
            # ---------------------------------------------------------------------

            # 01. make table row list
            c_elem_row_list = make_row_list(c_elem_list)

            # gridView, trigger 행을 분리한다.
            all_rows_seperated = seperate_rows_by_grid_and_trigger(c_elem_row_list)

            # group_table 의 top, height 임시 저장.
            i_group_top = group_table.top
            i_group_height = group_table.height

            # 새로 추가된 group 의 top, height 를 고려하여 기존 하위 group 의 top 갱신
            group_wq_siblings = [getEqElement(g) for g in group_table.element.parentNode.childNodes]
            group_wq_siblings.sort(key=lambda x: (x.top, x.height))
            group_wq_siblings_b = [g for g in group_wq_siblings if g.top > i_group_top]

            # group height 합계
            i_group_height_tot = 0

            for i, c_elem_row_list in enumerate(all_rows_seperated):

                group_table_c = None

                if i == 0:

                    # group 이 여러개인 경우
                    if len(all_rows_seperated) == 1:
                        group_table_c = group_table

                        # top 값을 변경한다.
                        i_new_top = i_group_top
                    else:
                        # group table 복사
                        group_table_c = copy_group_table(document, group_table, i)
                        # 부모 group 에 추가
                        group_table.element.appendChild(group_table_c.element)

                        # top 값을 변경한다.
                        i_new_top = 0


                    # # top 값을 변경한다.
                    # i_new_top = i_group_top
                    # 업데이트 top
                    updateTop(group_table_c, i_new_top)

                    # -----------------------------------------------------------

                    # gridView, 일반 table 분리 처리.
                    if len(c_elem_row_list) > 0:

                        grid_cnt = len([c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])

                        if grid_cnt > 0:

                            o_grid_view = [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"][0]

                            # height 값을 변경한다.
                            updateHeight(group_table_c, o_grid_view.height)

                            # height 합계
                            i_group_height_tot = (o_grid_view.height + config.group_space_extra)
                        else:
                            # height 값을 변경한다.
                            updateHeight(group_table_c, len(c_elem_row_list) * config.row_height)

                            # height 합계
                            i_group_height_tot = ((len(c_elem_row_list) * config.row_height) + (len(c_elem_row_list) * config.group_space_extra) + config.group_space_extra)

                elif i > 0:

                    # group table 복사
                    group_table_c = copy_group_table(document, group_table, i)

                    # TODO : 추가 확인
                    # 부모 group 에 추가
                    group_table.element.appendChild(group_table_c.element)
                    
                    # # top 값을 변경한다.
                    # i_new_top = i_group_top + i_group_height_tot
                    # top 값을 변경한다. (상대좌표이므로 i_group_top 제외)
                    i_new_top = i_group_height_tot

                    # 업데이트 top
                    updateTop(group_table_c, i_new_top)

                    # gridView, 일반 table 분리 처리.
                    if len(c_elem_row_list) > 0:

                        grid_cnt = len([c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])

                        if grid_cnt > 0:

                            o_grid_view = [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"][0]

                            # height 값을 변경한다.
                            updateHeight(group_table_c, o_grid_view.height)

                            # height 합계
                            i_group_height_tot += (o_grid_view.height + config.group_space_extra)
                        else:
                            # height 값을 변경한다.
                            updateHeight(group_table_c, len(c_elem_row_list) * config.row_height)

                            # height 합계
                            i_group_height_tot += ((len(c_elem_row_list) * config.row_height) + (len(c_elem_row_list) * config.group_space_extra) + config.group_space_extra)


                    # 마지막 row 의 경우만 실행
                    if i == (len(all_rows_seperated) - 1):

                        # height 값을 변경한다.
                        updateHeight(group_table, i_group_height_tot)
                        # background-color 삭제
                        removeStyleInfo(group_table, "background-color")

                # 02. th, td node 를 정의한다.
                define_th_td_node(c_elem_row_list)

                # 03. Table attribute/summary 추가
                add_attributes_and_summary(document, group_table_c)

                # group table 을 구성한다.
                make_group_table(document, group_table_c, c_elem_row_list)

            # gridView height 합계와
            # gridView 를 제외한 row count 를 가지고 전체 group_table 의 height 를 구한다.
            i_row_cnt = 0
            i_grid_height = sum([c.height for c in c_elem_list if c.localName == "gridView" and c.display != "none"])
            for i, c_elem_row_list in enumerate(all_rows_seperated):
                for row in c_elem_row_list:
                    grid_cnt = len([c for c in row if c.localName == "gridView" and c.display != "none"])
                    if grid_cnt == 0:
                        i_row_cnt += 1

            # 기존 group 의 height 와 비교
            i_height_diff = (i_row_cnt * config.row_height) + \
                            (i_row_cnt * config.group_space_extra) + i_grid_height - i_group_height

            # group_table 에 대한 처리가 끝나고 나서
            # 나머지 group 에 대한 height 업데이트 처리를 해 준다.
            for qq, wk_c in enumerate(group_wq_siblings_b):
                updateTop(wk_c, wk_c.top + i_height_diff + (len(all_rows_seperated) - 1) * config.group_space)

    # ---------------------------------------------------------------
    # TODO : 삭제
    """
    wq_group_list = []
    # TODO : 삭제
    print("control_id:{}".format(group_table.control_id))
    # 각 group 별 top 정보를 다시 설정환다.
    parent_elem = group_table.element.parentNode
    for c in parent_elem.childNodes:
        c_elem = getEqElement(c)
        wq_group_list.append(c_elem)
        # print("group info:localName:{},control_id:{},display:{},top:{}, left:{}, width:{},height:{}".format(c_elem.localName, c_elem.control_id, c_elem.display, c_elem.top, c_elem.left, c_elem.width, c_elem.height))
        print("group info:localName:{} / control_id:{} / display:{} / top:{} / left:{} / width:{} / height:{}".format(c_elem.localName, c_elem.control_id, c_elem.display, c_elem.top, c_elem.left, c_elem.width, c_elem.height))
    # ---------------------------------------------------------------
    wq_group_list.sort(key=lambda x: x.top)
    
    # child node 재구성
    for i, wq_c in enumerate(wq_group_list):
        parent_elem.removeChild(wq_c.element)
        parent_elem.appendChild(wq_c.element)
    # ---------------------------------------------------------------

    print("==========================================================================================================")

    if group_table.control_id == "1463":
        print()

    # top value
    i_top_val = 0

    # 각 group 별 top 정보를 다시 설정환다.
    parent_elem = group_table.element.parentNode
    for c in parent_elem.childNodes:
        c_elem = getEqElement(c)

        if i_top_val == 0:
            i_top_val = c_elem.top

        # 각 group 별로 group_space 를 띄운다.
        i_top_val = c_elem.height + config.group_space

        # update top
        # updateTop(c_elem, i_top_val)

        # print("group info:localName:{},control_id:{},display:{},top:{}, left:{}, width:{},height:{}".format(c_elem.localName, c_elem.control_id, c_elem.display, c_elem.top, c_elem.left, c_elem.width, c_elem.height))
        print("group info:localName:{} / control_id:{} / display:{} / top:{} / left:{} / width:{} / height:{}".format(c_elem.localName, c_elem.control_id, c_elem.display, c_elem.top, c_elem.left, c_elem.width, c_elem.height))
    """


"""
    th, td, inputCalendar tag element 생성
"""


def add_element_by_tag(document, tag):
    tag_element = None

    if tag == "th":
        # group th 생성
        tag_element = document.createElement("xf:group")
        tag_element.setAttribute("tagname", "th")
        tag_element.setAttribute("class", "w2tb_th")

    elif tag == "td":
        # group td 생성
        tag_element = document.createElement("xf:group")
        tag_element.setAttribute("tagname", "td")
        tag_element.setAttribute("class", "w2tb_td")

    elif tag == "inputCalendar":
        tag_element = document.createElement("w2:inputCalendar")
        tag_element.setAttribute("footerDiv", "false")
        tag_element.setAttribute("id", "")
        tag_element.setAttribute("style", "width: 150px;height: 23px;")
        tag_element.setAttribute("renderDiv", "true")
        tag_element.setAttribute("focusOnDateSelect", "false")
        tag_element.setAttribute("calendarValueType", "yearMonthDate")
        tag_element.setAttribute("rightAlign", "false")
        tag_element.setAttribute("renderType", "component")

    return tag_element


"""
    Element 의 Style 을 업데이트 한다.
"""


def updateStyle(wq_elem, group):
    # Element 의 left, top value 수정
    rel_left = wq_elem.left - group.left
    rel_top = wq_elem.top - group.top

    # 원본 element
    elem = wq_elem.element

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

        # Style 추출
        style_arr = style_str.split(";")

        for i, style_elem in enumerate(style_arr):
            if len(style_elem.strip()) == 0:
                continue

            # Element split (['width', '942px'])
            s_elem_arr = style_elem.strip().split(":")
            # style_name ('width')
            style_name = s_elem_arr[0].strip()

            if style_name == "left":
                s_elem_arr[1] = "{}px".format(rel_left)
            if style_name == "top":
                s_elem_arr[1] = "{}px".format(rel_top)

            # Style 요소 업데이트
            style_arr[i] = ":".join(s_elem_arr)

        # Style 업데이트
        elem.attributes["style"] = ";".join(style_arr)


"""
    Element Style 의 position 정보 (left, top, height) 를 삭제한다.
"""


def removePositionInfo(wq_elem):
    # 원본 element
    elem = wq_elem.element

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

        # Style 추출
        style_arr = style_str.split(";")

        # remove list : left, top, width, height
        remove_list = []

        for i, style_elem in enumerate(style_arr):
            if len(style_elem.strip()) == 0:
                continue

            # gridView 의 height 는 삭제하지 않는다.
            if elem.localName == "gridView" and "height" in style_elem:
                continue

            # position 정보 중에서 width 제외한 left, top, height 문자열 체크하며
            # remove_list 에 추가
            # textbox 의 width 는 삭제하지 않는다.
            if "position" in style_elem \
                    or "left" in style_elem \
                    or "top" in style_elem \
                    or "height" in style_elem \
                    or ("width" in style_elem and elem.localName == "textbox"):

                # or "width" in style_elem \
                remove_list.append(style_elem)

        # style array 에서 remove_list 항목 삭제.
        for p_info in remove_list:
            style_arr.remove(p_info)

        # Style 업데이트
        elem.attributes["style"] = ";".join(style_arr)


"""
    Element Style 의 특정 Style 정보 (left, top, height, width, background-color 대상) 를 삭제한다.
"""


def removeStyleInfo(wq_elem, style_target):
    # 원본 element
    elem = wq_elem.element

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

        # Style 추출
        style_arr = style_str.split(";")

        # remove list : left, top, width, height, background-color
        remove_list = []

        for i, style_elem in enumerate(style_arr):
            if len(style_elem.strip()) == 0:
                continue

            # 지정된 style 요소만 삭제하고 나머지 skip
            if style_target not in style_elem:
                continue

            # position 정보 중에서 width 제외한 left, top, height, background-color 문자열 체크하며
            # remove_list 에 추가
            # textbox 의 width 는 삭제하지 않는다.
            if "position" in style_elem \
                    or "left" in style_elem \
                    or "top" in style_elem \
                    or "height" in style_elem \
                    or "width" in style_elem \
                    or "background-color" in style_elem:

                # or "width" in style_elem \
                remove_list.append(style_elem)

        # style array 에서 remove_list 항목 삭제.
        for p_info in remove_list:
            style_arr.remove(p_info)

        # Style 업데이트
        elem.attributes["style"] = ";".join(style_arr)


"""
    Get xf_group_list
"""


def get_xf_group_list(document):
    # xf_group_list
    xf_group_list = []

    xf_group_arr = document.getElementsByTagName("xf:group")
    for g in xf_group_arr:

        # childNodes 가 없으면 skip
        if len(g.childNodes) == 0:
            continue

        # EqElement 를 만든다.
        g_elem = getEqElement(g)

        # Group 목록 추가
        xf_group_list.append(g_elem)

    return xf_group_list


"""
    Node 검색 및 정렬
"""


def search_and_rearrange_nodes(node):
    
    # 1. 자식 Node 가 존재하고.
    # 2. localName 이 trigger, gridView, select1, select 가 아니면. (즉, 자식 node 가 존재하지만 최종 node 에 해당하는 경우)
    if len(node.childNodes) > 0 and (node.localName not in config.localname_last_node_arr):

        # id = pnlLocator
        # 자식 Node 를 left, top 으로 정렬.
        re_arrange_elements(node)

        # Node 검색
        for child in node.childNodes:

            # search child nodes
            search_and_rearrange_nodes(child)


"""
    save result xml
"""


def save_result_xml(document, result_xml_file_name):
    result_xml = open(result_xml_file_name, "w", encoding="utf-8")
    xml_obj = xml.dom.minidom.parseString(document.toxml())
    xml_pretty_str = xml_obj.toprettyxml()
    result_xml.write(xml_pretty_str)
    result_xml.close()


"""
    Make row arrays
"""


def make_row_list(c_list):
    # top 정렬
    c_list.sort(key=lambda x: x.top)

    # top 목록 구성
    top_list = [c.top for c in c_list]

    # top 으로 rows 구성
    row_breaks = [i for i, (a, b) in enumerate(zip(top_list, top_list[1:]), 1) if b - a > config.row_threshold]
    top_row_groups = [top_list[s:e] for s, e in zip([0] + row_breaks, row_breaks + [None])]

    # 테이블 row 별 목록
    c_elem_row_list = []

    # hidden 항목 (row 의 모든 항목이 hidden 인 경우 마지막 row 에 한꺼번에 추가)
    c_hidden_elem_list = []

    # Loop : row
    i_start = 0
    if len(top_row_groups) > 0:
        for top_row in top_row_groups:
            # row 목록을 left 로 정렬.
            c_list_row = list(c_list[i_start:i_start + len(top_row)])
            c_list_row.sort(key=lambda x: x.left)

            # TODO : 테스트중
            # hidden row check (row 의 모든 element 가 hidden 인 경우 마지막에 추가)
            if len([c for c in c_list_row if c.display != "none" and c.visibility != "hidden"]) == 0:
                # hidden row 추가
                c_hidden_elem_list += c_list_row
                # i_start 증가
                i_start = i_start + len(top_row)
                continue

            # set row element list
            c_elem_row_list.append(c_list_row)
            # i_start 증가
            i_start = i_start + len(top_row)

        # TODO : 테스트중
        # hidden row element 추가
        if len(c_hidden_elem_list) > 0:
            c_elem_row_list[-1] += c_hidden_elem_list

        # set siblings
        for row in c_elem_row_list:
            for c in row:
                c.siblings = row

    return c_elem_row_list


"""
    Make row arrays for display
"""


def make_row_list_display(c_list):
    # trigger, display:none, visibility:hidden 을 제외
    c_list = [c for c in c_list if c.localName not in ["trigger"] and c.display != "none" and c.visibility != "hidden"]

    return make_row_list(c_list)


"""
    file_name 에서 result file_name 을 가져온다.
"""


def get_source_and_result_file_name(file_name):

    root = "/".join(file_name.split("/")[:-1])
    file = file_name.split("/")[-1]

    source_xml_file_name: str = "{}/{}".format(root, file)

    # "convert" 가 포함된 경우 삭제 후 skip
    if "convert" in file:
        if os.path.isfile(source_xml_file_name):
            os.remove(source_xml_file_name)

    result_xml_file_name = "{}/{}-convert.xml".format(root, file.split(".")[0])

    return source_xml_file_name, result_xml_file_name


"""
    get recursive files list
"""


def get_file_list(dir_path):
    directory = dir_path
    pathname = directory + "/**/*.xml"
    files = glob.glob(pathname, recursive=True)
    return files


"""
    directory 검색하여 source 와 result file 경로 목록을 만든다.
    파일명에 convert 문자열 포함인 경우 제외.
"""


def get_files_by_dir(dir_path):
    source_xml_file_name_list = []
    result_xml_file_name_list = []

    # get recursive files list
    files = get_file_list(dir_path)

    for file_name in files:

        # Windows 파일 경로가 존재하는 경우 대응.
        file_name = "/".join(file_name.split("\\"))

        if file_name.endswith('.xml'):

            # 경로와 file명 분리
            root = "/".join(file_name.split("/")[:-1])
            file = file_name.split("/")[-1]

            # source file 경로
            source_xml_file_name: str = "{}/{}".format(root, file)

            # "convert" 가 포함된 경우 삭제 후 skip
            if "convert" in file:
                if os.path.isfile(source_xml_file_name):
                    os.remove(source_xml_file_name)
                continue

            result_xml_file_name = "{}/{}-convert.xml".format(root, file.split(".")[0])

            source_xml_file_name_list.append(source_xml_file_name)
            result_xml_file_name_list.append(result_xml_file_name)

    return source_xml_file_name_list, result_xml_file_name_list


'''
    get current date (yyyymmdd)
'''


def get_curr_date_yyyymmdd():
    # datetime.today().strftime("%Y%m%d%H%M%S")    # YYYYmmddHHMMSS 형태의 시간 출력
    curr_date_yyyymmdd = datetime.today().strftime("%Y%m%d")
    return curr_date_yyyymmdd


'''
    get current date (yyyymmddHHmmss)
'''


def get_curr_date_yyyymmddhhmmss():
    # datetime.today().strftime("%Y%m%d%H%M%S")    # YYYYmmddHHMMSS 형태의 시간 출력
    curr_date_yyyymmdd = datetime.today().strftime("%Y%m%d%H%M%S")
    return curr_date_yyyymmdd


'''
    get current date (yyyy-mm-dd hh:mi:ss)
'''


def get_curr_date_yyyymmdd_hhmiss():
    curr_date_yyyymmdd_hhmiss = datetime.today().strftime("%Y-%m-%d %H:%M:%S")  # YYYYmmddHHMMSS 형태의 시간 출력
    return curr_date_yyyymmdd_hhmiss


# TODO : 삭제 (사용안함)
def set_logging_basic_config():
    logging.basicConfig(filename='{}_file.log'.format(get_curr_date_yyyymmddhhmmss()),
                        level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s', encoding="utf-8")


"""
    WebSquare file 변환 (절대좌표 ▶ 상대좌표)
"""


def convert_wq_file(source_xml_file_name, result_xml_file_name):
    # Parse XML
    document = parse(source_xml_file_name)

    # body Element 조회
    body_root = document.getElementsByTagName("body")[0]

    # minidom 의 공백 제거
    search_and_remove_space(document)

    # Element 검색 및 재배치
    search_and_rearrange_nodes(body_root)

    # Group 과 Element 재구성.
    search_and_regroup_nodes(document)

    # XML 저장
    save_result_xml(document, result_xml_file_name)
