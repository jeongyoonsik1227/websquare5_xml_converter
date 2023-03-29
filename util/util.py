# -*- coding: utf-8 -*-
import os
import xml
from datetime import datetime
import logging
import glob
from xml.dom.minidom import parse
from collections.abc import Iterable
import re
from . import config

'''
    element의 left, top, width, height 정보 보관
'''


class WqElement:
    def __init__(self, element=None):
        # element
        self.element = element
        # next element
        self.next_element = None

        # Member variables
        self.class_str = ""
        self.id = ""
        self.label = ""
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
        self.col_span = 0
        self.row_span = 0
        self.id_index = 0

    def setClass(self, class_str):
        self.element.setAttribute("class", class_str)
        self.class_str = class_str


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
    wq_element.label = attributes_and_style_map["label"]
    wq_element.control_id = attributes_and_style_map["control_id"]
    wq_element.class_str = attributes_and_style_map["class"]
    wq_element.dataType = attributes_and_style_map["dataType"]
    wq_element.allOption = attributes_and_style_map["allOption"]

    # id 에서 숫자를 추출한 결과
    if len(wq_element.id) > 0:
        wq_element.id_index = int(get_digit(wq_element.id))

    # ETC
    if hasattr(elem, "nodeName"):
        if elem.nodeName not in ["#cdata-section", "#comment"]:
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
    if hasattr(elem, "attributes"):
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
        childNodes_copy = elem.childNodes.copy()
        for e in list(childNodes_copy):

            # 기존 삭제
            elem.removeChild(e)

            # Element Node 만 추가
            if e.nodeType == config.ELEMENT_NODE:
                # EqElement를 만든다.
                wq_elem_list.append(getEqElement(e))

        # 01. make table row list
        c_elem_row_list = make_row_list(wq_elem_list)

        # 한 줄인 경우와 두 줄 이상인 경우 정렬기준이 달라진다.
        if len(c_elem_row_list) == 1:
            # Style 정보를 기반으로 업데이트 한다.
            # 단일행의 경우 left 정렬만.
            wq_elem_list.sort(key=lambda x: x.left)
        else:
            # Style 정보를 기반으로 업데이트 한다.
            # 복수행의 경우 top, left 정렬.
            wq_elem_list.sort(key=lambda x: (x.top, x.left))

        # Element 목록 추가.
        for wq_e in wq_elem_list:
            elem.appendChild(wq_e.element)


"""
    attributes 를 map 으로 return
"""


def get_attributes(elem):
    id_str = ""
    label_str = ""
    control_id_str = ""
    style_str = ""
    class_str = ""
    dataType_str = ""
    allOption_str = ""

    # attributes 세팅.
    if hasattr(elem, "attributes"):
        if elem.attributes:
            if elem.attributes.get("class"):
                class_str = elem.attributes.get("class").value
            if elem.attributes.get("id"):
                id_str = elem.attributes.get("id").value
            if elem.attributes.get("label"):
                label_str = elem.attributes.get("label").value
            if elem.attributes.get("control_id"):
                control_id_str = elem.attributes.get("control_id").value
            if elem.attributes.get("style"):
                style_str = elem.attributes.get("style").value
            if elem.attributes.get("dataType"):
                dataType_str = elem.attributes.get("dataType").value
            if elem.attributes.get("allOption"):
                allOption_str = elem.attributes.get("allOption").value

    attributes_map = {"class": class_str, "id": id_str, "label": label_str, "control_id": control_id_str,
                      "style": style_str, "dataType": dataType_str, "allOption": allOption_str}

    return attributes_map


"""
    minidom parser 에서 생성된 공백 Node 제거.
"""


def search_and_remove_space(node):
    if len(node.childNodes) > 0:

        child_list = list(node.childNodes.copy())
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
        childNodes_copy = p_node.childNodes.copy()
        for c in list(childNodes_copy):

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
                    c_left, c_top, c_width, c_height = c_elem.left, c_elem.top, c_elem.width, c_elem.height
                    c_center_x = c_left + int(c_width / 2)
                    c_center_y = c_top + int(c_height / 2)

                    # element 절대좌표 top, left 에 해당하는 group 을 찾는다.
                    if g_left < c_center_x < (g_left + g_width) and g_top < c_center_y < (g_top + g_height):
                        # group 에 child 노드를 추가한다. (절대좌표 필요)
                        append_eq_child_with_style(group, c_elem)

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
    group_table_class = group_table.element.getAttribute("class")
    # dfbox, 즉 좌우측으로 요소가 정렬 되어야 하는 경우가 아니면.
    # dfbox 가 있는 경우 group 을 이용한 table 을 만들지 않는다.
    if group_table_class != "dfbox":
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
    th_col_breaks = [i for i, (a, b) in enumerate(zip(th_left_list, th_left_list[1:]), 1) if
                     b - a > config.th_threshold]
    th_col_groups = [th_left_list[s:e] for s, e in zip([0] + th_col_breaks, th_col_breaks + [None])]

    # td left 목록
    td_left_list = [c.left for c in td_list]
    td_col_breaks = [i for i, (a, b) in enumerate(zip(td_left_list, td_left_list[1:]), 1) if
                     b - a > config.th_threshold]
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

        # th, td element 목록
        th_td_elem_list = []

        # th, td temp 항목
        th_td_temp = None

        # group_tr 에 th, td 컬럼 추가
        for i, th_td in enumerate(row[0].th_td_list):

            # th_td wq element
            th_td_elem = getEqElement(th_td)

            # td 열을 기준으로 blank 인 연속된 td 를 merge 하기 위한 colspan 의 길이를 구한다.
            if th_td_elem.class_str == "w2tb_td" and len(th_td.childNodes) > 0:
                th_td_temp = th_td_elem
                th_td_temp.col_span = 1

                # th/td element 목록에 추가
                th_td_elem_list.append(th_td_temp)

                # group_tr 에 추가
                group_tr.appendChild(th_td)

            if th_td_elem.class_str == "w2tb_td" and len(th_td.childNodes) == 0:
                if th_td_temp is None:
                    th_td_temp = th_td_elem
                    th_td_temp.col_span = 1
                    # th/td element 목록에 추가
                    th_td_elem_list.append(th_td_temp)

                    # group_tr 에 추가
                    group_tr.appendChild(th_td)
                else:
                    # col_span 1 증가
                    th_td_temp.col_span = th_td_temp.col_span + 1

            # th_td 가 "th" 인 경우 th_td_temp 초기화
            # group_tr 에 th_td 추가
            if th_td_elem.class_str == "w2tb_th":
                th_td_temp = None

                # group_tr 에 추가
                group_tr.appendChild(th_td)

            # th / td 의 col_span, row_span 구성
            if th_td == row[0].th_td_list[-1]:
                if len(th_td_elem_list) > 0:
                    for th_td_el in th_td_elem_list:
                        if th_td_el.col_span > 1:

                            # 자식 node list
                            childNodes_list = []

                            # 자식 node 제거
                            childNodes_copy = th_td_el.element.childNodes.copy()
                            for c in childNodes_copy:
                                c.parentNode.removeChild(c)
                                childNodes_list.append(c)

                            # col span, row span attributes 추가
                            # col span, row span attributes 가 다른 node 보다 앞에 위치.
                            add_span_attributes(document, th_td_el)

                            # 자식 node 추가
                            for c in childNodes_list:
                                th_td_el.element.appendChild(c)


"""
    group table 을 구성한다.
"""


def make_group_table(document, group_table, c_elem_row_list):
    # width 400px 이상인 group 이 존재하지 않는 경우만 table 생성.
    if has_large_group(c_elem_row_list):

        # class 가 sub_contents 가 아니면 삭제.
        if group_table.class_str != "sub_contents":
            # 현재 group 삭제
            group_table.element.parentNode.removeChild(group_table.element)

    else:
        # 02. th, td node 를 정의한다.
        define_th_td_node(c_elem_row_list)

        # 03. Table attribute/summary 추가
        add_attributes_and_summary(document, group_table)

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

        # table group 상위에 table class group 으로 한 번 감싼다.
        wrap_group_table(document, group_table)


"""
    th, td 컬럼 타입을 정한다.
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

            # # TODO : 추가
            # # col_member 대상으로 "group", "tabControl", "gridView" 제외.
            # if c.localName in ["group", "tabControl", "gridView"]:
            #     continue

            # row 에 textbox 가 없으면.
            # 그리고 첫번째이면.
            if len([x for x in row if x.localName == "textbox"]) == 0 and jj == 0:
                c.col_type = "td"
                c.col_members.append(c)
                c_tmp = c

            # textbox 다음 항목이 hidden 인 경우.
            elif len(hidden_list) > 0:
                if not is_hidden(c):
                    c.col_type = "td"
                    c.col_members.append(c)
                    c.col_members += hidden_list
                    c_tmp = c
                    hidden_list = []
                else:
                    hidden_list.append(c)

            # th 최소폭 보다 크면서 textbox 이면.
            elif not is_hidden(c) \
                    and c.localName == "textbox" \
                    and c.width > config.least_th_width:
                c.col_type = "th"
                c.col_members.append(c)
                c_tmp = c

            # 이전 member 가 th 이면.
            elif not is_hidden(c) \
                    and row[jj - 1].col_type == "th":
                c.col_type = "td"
                c.col_members.append(c)
                c_tmp = c

            # hidden 이고 이전이 th 이면.
            elif is_hidden(c) \
                    and row[jj - 1].col_type == "th":
                hidden_list.append(c)

            # (i-1).right 와 left 차이가 '30px' 보다 크면(벌어져 있으면).
            else:
                if not is_hidden(c) \
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

    # class
    # TODO : 테스트중 (class setting 시점의 문제 검토 중...)
    # if elem.attributes:
    #     group_table_tmp.setAttribute("class", config.tbl_class)

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
        # 3. row 에 700px 이상의 group 이 존재하면.
        if len([c for c in row if c.localName == "gridView" and not is_hidden(c)]) > 0 \
                or len([c for c in row if c.localName == "trigger"]) == len(row) \
                or len(
            [c for c in row if c.localName == "group" and c.width > config.min_group_width and not is_hidden(c)]) > 0:

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
    for i, g in enumerate(xf_group_list):
        if g.element.childNodes == group_table.element.childNodes:
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
    for idx, group_table in enumerate(xf_group_list):

        # TODO : 테스트중
        # class 가 'dfbox' 인 것은 이미 처리가 완료된 것이므로 제외.
        # 2022.11.21 추가
        if group_table.class_str in ["dfbox", "lybox", "div_table"]:
            continue

        c_elem_row_list = []
        c_elem_left_min = []

        # group 이면서 width 가 700px 이상.
        # textbox 가 하나 이상.
        # if group_table.width > 700 and len([c for c in group_table.element.childNodes if c.localName == "textbox"]) > 0:
        # if len(group_table.element.childNodes) > 0:
        # if group_table.width > 700:
        if group_table.width >= config.min_group_width:

            group_table = get_latest_group_table(body_root, group_table)

            # group_table 이 None 이면 skip.
            if group_table is None:
                continue

            try:
                # Group element 의 wq element child list 를 만든다.
                c_elem_list = [getEqElement(c) for c in group_table.element.childNodes]
            except Exception as e:
                print(e)

            # 자식 node 모두 삭제 (자식 node 가 group 인 경우는 제외.)
            childNodes_copy = group_table.element.childNodes.copy()
            for c in list(childNodes_copy):
                # 자식 node 가 group 인 경우는 삭제하지 않는다.
                if c.localName == "group":
                    continue
                # 자식 node 삭제.
                group_table.element.removeChild(c)

            # 01. make table row list
            c_elem_row_list = make_row_list(c_elem_list)

            # gridView, trigger 행을 분리한다.
            all_rows_seperated = seperate_rows_by_grid_and_trigger(c_elem_row_list)

            # group_table 의 top, height 임시 저장.
            i_group_top = group_table.top
            i_group_height = group_table.height

            # 새로 추가된 group 의 top, height 를 고려하여 기존 하위 group 의 top 갱신
            group_wq_siblings = [getEqElement(g) for g in group_table.element.parentNode.childNodes if
                                 g.nodeName != "#comment"]
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

                    # 업데이트 top
                    updateTop(group_table_c, i_new_top)

                    # gridView, 일반 table 분리 처리.
                    if len(c_elem_row_list) > 0:

                        grid_cnt = len(
                            [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])

                        if grid_cnt > 0:

                            o_grid_view = \
                                [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"][0]

                            # height 값을 변경한다.
                            updateHeight(group_table_c, o_grid_view.height)

                            # height 합계
                            i_group_height_tot = (o_grid_view.height + config.group_space_extra)
                        else:
                            # height 값을 변경한다.
                            updateHeight(group_table_c, len(c_elem_row_list) * config.row_height)

                            # height 합계
                            i_group_height_tot = ((len(c_elem_row_list) * config.row_height) + (
                                    len(c_elem_row_list) * config.group_space_extra) + config.group_space_extra)

                elif i > 0:

                    # group table 복사
                    group_table_c = copy_group_table(document, group_table, i)

                    # 부모 group 에 추가
                    group_table.element.appendChild(group_table_c.element)

                    # top 값을 변경한다.
                    i_new_top = i_group_height_tot

                    # 업데이트 top
                    updateTop(group_table_c, i_new_top)

                    # gridView, 일반 table 분리 처리.
                    if len(c_elem_row_list) > 0:

                        grid_cnt = len(
                            [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])

                        if grid_cnt > 0:

                            o_grid_view = \
                                [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"][0]

                            # height 값을 변경한다.
                            updateHeight(group_table_c, o_grid_view.height)

                            # height 합계
                            i_group_height_tot += (o_grid_view.height + config.group_space_extra)
                        else:
                            # height 값을 변경한다.
                            updateHeight(group_table_c, len(c_elem_row_list) * config.row_height)

                            # height 합계
                            i_group_height_tot += ((len(c_elem_row_list) * config.row_height) + (
                                    len(c_elem_row_list) * config.group_space_extra) + config.group_space_extra)

                    # 마지막 row 의 경우만 실행
                    if i == (len(all_rows_seperated) - 1):
                        # height 값을 변경한다.
                        updateHeight(group_table, i_group_height_tot)
                        # background-color 삭제
                        removeStyleInfo(group_table, "background-color")

                # gridView, tabControl, treeView, table 에 대해서 group 에 구성요소 별 class 적용.
                grid_cnt = len([c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])
                tab_cnt = len([c for c in c_elem_row_list[0] if c.localName == "tabControl" and c.display != "none"])
                tree_cnt = len([c for c in c_elem_row_list[0] if c.localName == "treeView" and c.display != "none"])

                if (grid_cnt + tab_cnt + tree_cnt) > 0:
                    if grid_cnt > 0:
                        # group 에 기존 setting 된 class 가 존재하는 경우 하위에 group 추가.
                        insert_or_set_group_class(document, group_table_c, ["lybox", "ly_column"], config.gvw_class)
                        # group 에 배열 형태의 child 를 추가한다. (절대좌표 수정 없음)
                        append_child_element_by_array(group_table_c, c_elem_row_list[0])
                    elif tab_cnt > 0:
                        # group 에 기존 setting 된 class 가 존재하는 경우 하위에 group 추가.
                        insert_or_set_group_class(document, group_table_c, ["lybox", "ly_column"], config.tab_class)
                        # group 에 배열 형태의 child 를 추가한다. (절대좌표 수정 없음)
                        append_child_element_by_array(group_table_c, c_elem_row_list[0])
                    elif tree_cnt > 0:
                        # group 에 기존 setting 된 class 가 존재하는 경우 하위에 group 추가.
                        insert_or_set_group_class(document, group_table_c, ["lybox", "ly_column"], config.tvw_class)
                        # group 에 배열 형태의 child 를 추가한다. (절대좌표 수정 없음)
                        append_child_element_by_array(group_table_c, c_elem_row_list[0])

                # dfbox group 대상인지 확인.
                # 1. 한 줄 group 이고.
                # 2. "gridView", "input", "select1", "select" 등이 없으면 True 를 반환.
                if is_dfbox_group(c_elem_row_list):

                    is_dfbox_group(c_elem_row_list)

                    # 조건에 만족하면 group 에 "dfbox" class 를 추가한다.
                    group_table_c.setClass(config.dfbox_class)

                    # base_group
                    base_group = body_root.childNodes[0]

                    # 근접한 요소들을 묶어서 하나의 col_members 로 만든다.
                    define_col_members(c_elem_row_list)

                    make_dfbox_group(document, c_elem_row_list[0], base_group, g_elem_param=group_table_c)

                elif group_table_c.class_str not in ["tbbox", "tabbox", "tvwbox", "gvwbox", "div_table"]:

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


"""
    개별 Group 재구성
"""


def restruct_group(document, group_table):
    # body Element 조회
    body_root = document.getElementsByTagName("body")[0]

    c_elem_row_list = []
    c_elem_left_min = []

    try:
        # Group element 의 wq element child list 를 만든다.
        c_elem_list = [getEqElement(c) for c in group_table.element.childNodes]
    except Exception as e:
        print(e)

    # 자식 node 모두 삭제 (자식 node 가 group 인 경우는 제외.)
    childNodes_copy = group_table.element.childNodes.copy()
    for c in list(childNodes_copy):
        # 자식 node 가 group 인 경우는 삭제하지 않는다.
        if c.localName == "group":
            continue
        # 자식 node 삭제.
        group_table.element.removeChild(c)

    # 01. make table row list
    c_elem_row_list = make_row_list(c_elem_list)

    # gridView, trigger 행을 분리한다.
    all_rows_seperated = seperate_rows_by_grid_and_trigger(c_elem_row_list)

    # group_table 의 top, height 임시 저장.
    i_group_top = group_table.top
    i_group_height = group_table.height

    # 새로 추가된 group 의 top, height 를 고려하여 기존 하위 group 의 top 갱신
    group_wq_siblings = [getEqElement(g) for g in group_table.element.parentNode.childNodes if g.nodeName != "#comment"]
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

            # gridView, 일반 table 분리 처리.
            if len(c_elem_row_list) > 0:

                grid_cnt = len(
                    [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])

                if grid_cnt > 0:

                    o_grid_view = \
                        [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"][0]

                    # height 값을 변경한다.
                    updateHeight(group_table_c, o_grid_view.height)

                    # height 합계
                    i_group_height_tot = (o_grid_view.height + config.group_space_extra)
                else:
                    # height 값을 변경한다.
                    updateHeight(group_table_c, len(c_elem_row_list) * config.row_height)

                    # height 합계
                    i_group_height_tot = ((len(c_elem_row_list) * config.row_height) + (
                            len(c_elem_row_list) * config.group_space_extra) + config.group_space_extra)

        elif i > 0:

            # group table 복사
            group_table_c = copy_group_table(document, group_table, i)
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

                grid_cnt = len(
                    [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])

                if grid_cnt > 0:

                    o_grid_view = \
                        [c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"][0]

                    # height 값을 변경한다.
                    updateHeight(group_table_c, o_grid_view.height)

                    # height 합계
                    i_group_height_tot += (o_grid_view.height + config.group_space_extra)
                else:
                    # height 값을 변경한다.
                    updateHeight(group_table_c, len(c_elem_row_list) * config.row_height)

                    # height 합계
                    i_group_height_tot += ((len(c_elem_row_list) * config.row_height) + (
                            len(c_elem_row_list) * config.group_space_extra) + config.group_space_extra)

            # 마지막 row 의 경우만 실행
            if i == (len(all_rows_seperated) - 1):
                # height 값을 변경한다.
                updateHeight(group_table, i_group_height_tot)
                # background-color 삭제
                removeStyleInfo(group_table, "background-color")

        # gridView, tabControl, treeView, table 에 대해서 group 에 구성요소 별 class 적용.
        grid_cnt = len([c for c in c_elem_row_list[0] if c.localName == "gridView" and c.display != "none"])
        tab_cnt = len([c for c in c_elem_row_list[0] if c.localName == "tabControl" and c.display != "none"])
        tree_cnt = len([c for c in c_elem_row_list[0] if c.localName == "treeView" and c.display != "none"])

        if (grid_cnt + tab_cnt + tree_cnt) > 0:
            if grid_cnt > 0:
                # group 에 기존 setting 된 class 가 존재하는 경우 하위에 group 추가.
                insert_or_set_group_class(document, group_table_c, ["lybox", "ly_column"], config.gvw_class)
                # group 에 배열 형태의 child 를 추가한다. (절대좌표 수정 없음)
                append_child_element_by_array(group_table_c, c_elem_row_list[0])
            elif tab_cnt > 0:
                # group 에 기존 setting 된 class 가 존재하는 경우 하위에 group 추가.
                insert_or_set_group_class(document, group_table_c, ["lybox", "ly_column"], config.tab_class)
                # group 에 배열 형태의 child 를 추가한다. (절대좌표 수정 없음)
                append_child_element_by_array(group_table_c, c_elem_row_list[0])
            elif tree_cnt > 0:
                # group 에 기존 setting 된 class 가 존재하는 경우 하위에 group 추가.
                insert_or_set_group_class(document, group_table_c, ["lybox", "ly_column"], config.tvw_class)
                # group 에 배열 형태의 child 를 추가한다. (절대좌표 수정 없음)
                append_child_element_by_array(group_table_c, c_elem_row_list[0])

        # group 중에 component 가 있는 지를 체크한다.
        if has_one_group_with_component(c_elem_row_list[0]):

            # group 을 가져온다.
            c_group = [c for c in c_elem_row_list[0] if c.localName == "group" and not is_hidden(c)][0]
            # group 의 부모/자식 제거.
            c_group.element.parentNode.removeChild(c_group.element)

            # childNode 를 c_group 에서 group_table_c 로 이동.
            childNodes_copy = c_group.element.childNodes.copy()
            for c in childNodes_copy:
                c_group.element.removeChild(c)
                group_table_c.element.appendChild(c)

            # group 과 동일 Level에 있는 component 이동.
            c_comp_list = [c for c in c_elem_row_list[0] if c.localName != "group"]
            for c in c_comp_list:
                group_table_c.element.appendChild(c.element)

            # group 구성 재귀 호출.
            restruct_group(document, group_table_c)

        # dfbox group 대상인지 확인.
        # 1. 한 줄 group 이고.
        # 2. "gridView", "input", "select1", "select" 등이 없으면 True 를 반환.
        elif is_dfbox_group(c_elem_row_list):

            # 조건에 만족하면 group 에 "dfbox" class 를 추가한다.
            group_table_c.setClass(config.dfbox_class)

            # base_group
            base_group = body_root.childNodes[0]

            # 근접한 요소들을 묶어서 하나의 col_members 로 만든다.
            define_col_members(c_elem_row_list)

            # dfbox group 구성.
            make_dfbox_group(document, c_elem_row_list[0], base_group, g_elem_param=group_table_c)

        elif group_table_c.class_str not in ["tbbox", "tabbox", "tvwbox", "gvwbox"]:

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


def update_position_info(wq_elem, group):
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

        # absolute 의 경우만 적용.
        if "position:absolute" in style_arr:

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

            # gridView, image 의 height 는 삭제하지 않는다.
            if elem.localName in ["gridView", "image"] and "height" in style_elem:
                continue

            # position 정보 중에서 width 제외한 left, top, height 문자열 체크하며
            # remove_list 에 추가
            if "position" in style_elem \
                    or "left" in style_elem \
                    or "top" in style_elem \
                    or "height" in style_elem:
                remove_list.append(style_elem)

        # style array 에서 remove_list 항목 삭제.
        for p_info in remove_list:
            style_arr.remove(p_info)

        # Style 업데이트
        elem.attributes["style"] = ";".join(style_arr)


"""
    Element Style 의 특정 Style 정보 (position, left, top, width, height, background-color, border-color 대상) 를 삭제한다.
"""


def removeStyleInfo(wq_elem, style_target):
    # 원본 element
    elem = wq_elem.element

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

        # Style 추출
        style_arr = style_str.split(";")

        # remove list : position, left, top, width, height, background-color, border-color
        remove_list = []

        for i, style_elem in enumerate(style_arr):
            if len(style_elem.strip()) == 0:
                continue

            # 지정된 style 요소만 삭제하고 나머지 skip
            if style_target not in style_elem:
                continue

            # position 정보 중에서 position, left, top, width, height, background-color, border-color 문자열 체크하며
            # remove_list 에 추가
            if "position" == get_first(style_elem, ":") \
                    or "left" == get_first(style_elem, ":") \
                    or "top" == get_first(style_elem, ":") \
                    or "width" == get_first(style_elem, ":") \
                    or "height" == get_first(style_elem, ":") \
                    or "background" == get_first(style_elem, ":") \
                    or "background-color" == get_first(style_elem, ":") \
                    or "border-color" == get_first(style_elem, ":") \
                    or "border" == get_first(style_elem, ":") \
                    or "color" == get_first(style_elem, ":") \
                    or "font-family" == get_first(style_elem, ":") \
                    or "font-size" == get_first(style_elem, ":") \
                    or "text-align" == get_first(style_elem, ":") \
                    or "overflow" == get_first(style_elem, ":"):
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

        # Group 목록 추가
        xf_group_list.append(getEqElement(g))

    return xf_group_list


"""
    Node 검색 및 정렬
"""


def search_and_rearrange_nodes(node):
    # group 인 경우 siblings 들의 좌표를 확인하여 부모-자식 관계를 구성한다.
    if getEqElement(node).localName == "group" and not is_hidden(getEqElement(node)):
        # TODO : 확인 후 적용
        # 자식 node 가 하나이고 group 이면 제거한다. (불필요한 자식 group 을 제거한다.)
        search_and_remove_surplus_child_group(getEqElement(node))

        # 동일 Level 에 존재하는 group 과 기타 object 들의 관계를 재설정.
        rearrange_siblings_by_coordinate(node)

    # 1. 자식 Node 가 존재하고.
    # 2. localName 이 trigger, gridView, tabControl, select1, select 가 아니면. (즉, 자식 node 가 존재하지만 최종 node 에 해당하는 경우 제외.)
    if len(node.childNodes) > 0 and (node.localName not in config.localname_last_node_arr):

        # id = pnlLocator
        # 자식 Node 를 left, top 으로 정렬.
        # left, top 정렬을 위해, remove / appendChild 실행.
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
    # c_list, c_list_hidden 구성.
    c_list_hidden = list([c for c in c_list if is_hidden(c)])
    c_list_except_hidden = list(set(c_list) - set(c_list_hidden))

    # hidden 항목을 제외하여 row 를 만든다.
    c_list = c_list_except_hidden

    # top 정렬
    c_list.sort(key=lambda x: x.top)

    # top 목록 구성
    top_list = [c.top for c in c_list]

    # top 으로 rows 구성
    row_breaks = [i for i, (a, b) in enumerate(zip(top_list, top_list[1:]), 1) if b - a > config.row_threshold]
    top_row_groups = [top_list[s:e] for s, e in zip([0] + row_breaks, row_breaks + [None])]

    # 테이블 row 별 목록
    c_elem_row_list = []

    # Loop : row
    i_start = 0
    if len(top_row_groups) > 0:
        for top_row in top_row_groups:
            # row 목록을 left 로 정렬.
            # hidden 항목이 있는 경우, 배열에서 잘리는 현상을 수정.
            c_list_row = list(c_list[i_start:i_start + len(top_row)])
            c_list_row.sort(key=lambda x: x.left)

            # set row element list
            c_elem_row_list.append(c_list_row)
            # i_start 증가
            i_start = i_start + len(top_row)

        # hidden row element 마지막 row 에 추가
        if len(c_list_hidden) > 0:
            c_elem_row_list[-1] += c_list_hidden

        # set siblings
        for row in c_elem_row_list:
            for c in row:
                c.siblings = row

    return c_elem_row_list


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

    # base_group 을 만든다.
    # body root 를 check 하여 base_group 이 존재하지 않으면 추가.
    check_and_add_base_group(document, body_root)

    # Element 검색 및 재배치
    search_and_rearrange_nodes(body_root)

    # tabControl 의 content 에 group 이 없는 경우 추가.
    add_group_to_tab_content_child(document)

    # --------------------------------------------------------------------------------
    # div_table 구조를 찾아 재구성한다.
    find_div_table_and_restruct(document, body_root)
    # --------------------------------------------------------------------------------

    # lybox 대상을 찾아 재구성. (class 재설정, lybox, ly_column)
    find_lybox_and_restruct(document, body_root)

    # row 에 group 이 존재하면 재배치 하고, group 이 존재하지 않으면 새로운 group 추가.
    add_group_or_rearrange_child(document, body_root)

    # Group 과 Element 재구성.
    search_and_regroup_nodes(document)

    # Row 단위로 gridView, tabControl, treeView 에 대해서 class 지정과 함께 상위 group 추가.
    add_class_to_group_component(document, body_root)

    # position, top, left 스타일 제거.
    search_and_remove_position_info(body_root)

    # group, tabControl, gridView 의 style 에 존재하는 absolute, top, left 요소 삭제.
    removeAbsoluteAndStyle(body_root)

    # XML 저장
    save_result_xml(document, result_xml_file_name)


"""
    row 에 group 이 존재하면 재배치 하고, group 이 존재하지 않으면 새로운 group 추가.
"""


def add_group_or_rearrange_child(document, body_root):
    base_group = body_root.childNodes[0]

    # Group element 의 wq element child list 를 만든다.
    c_elem_list = [getEqElement(c) for c in base_group.childNodes]

    # 01. make table row list
    c_elem_row_list = make_row_list(c_elem_list)

    # 근접한 요소들을 묶어서 하나의 col_members 로 만든다.
    define_col_members(c_elem_row_list)

    # dfbox group 을 생성하고 group 에 child 를 추가한다.
    make_dfbox_group_and_arrange_child(document, base_group, c_elem_row_list)


"""
    새로운 group 을 생성한다.
    return EqElement group 을 반환한다.
"""


def get_new_group(document, g_parent=None, g_tyle="", g_class=""):
    # group 생성.
    g_new = document.createElement("xf:group")

    # group 속성 정의.
    if len(g_tyle) > 0:
        g_new.setAttribute("style", g_tyle)
    if len(g_class) > 0:
        g_new.setAttribute("class", g_class)

    # 부모 group 에 추가.
    if g_parent:
        g_parent.appendChild(g_new)

    return getEqElement(g_new)


"""
    group, tabControl, gridView 목록에서 max_width, min_left 를 구한다.
"""


def get_max_width_and_min_left(document):
    # 초기화.
    max_width = 0
    min_left = 0

    # group, tabControl, gridView 의 목록을 만든다.
    xf_group_arr = document.getElementsByTagName("xf:group")
    w2_tab_arr = document.getElementsByTagName("w2:tabControl")
    w2_grid_arr = document.getElementsByTagName("w2:gridView")

    # 배열을 합친다.
    group_arr = xf_group_arr + w2_tab_arr + w2_grid_arr

    if len(group_arr) > 0:
        # max width 를 구한다.
        max_width = max([getEqElement(g).width for g in group_arr])
        # min left 를 구한다.
        min_left = min([getEqElement(g).left for g in group_arr])

    return max_width, min_left


"""
    group, tabControl, gridView 의 style 에 존재하는 absolute, top, left, width 요소 삭제.
"""


def removeAbsoluteAndStyle(body_root):
    # body 에서 width Style 제거.
    removeStyleInfo(getEqElement(body_root), "width")

    # xf:group Element 조회
    xf_group_list = get_xf_group_list(body_root)
    for c_group in xf_group_list:
        removeStyleInfo(c_group, "position")
        removeStyleInfo(c_group, "top")
        removeStyleInfo(c_group, "left")
        removeStyleInfo(c_group, "width")
        removeStyleInfo(c_group, "height")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_group)

    # tabControl 스타일 정보 삭제
    xf_tab_arr = body_root.getElementsByTagName("w2:tabControl")
    xf_tab_list = list([getEqElement(t) for t in xf_tab_arr])
    for c_tab in xf_tab_list:
        # tabControl 에 class 추가 ('w2tabcontrol' --> 'w2tabcontrol wq_tab')
        c_tab.setClass("wq_tab")

        removeStyleInfo(c_tab, "position")
        removeStyleInfo(c_tab, "top")
        removeStyleInfo(c_tab, "left")
        removeStyleInfo(c_tab, "width")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_tab)

    # gridView 스타일 정보 삭제
    xf_grid_arr = body_root.getElementsByTagName("w2:gridView")
    xf_grid_list = list([getEqElement(t) for t in xf_grid_arr])
    for c_grid in xf_grid_list:
        # gridView 에 class 추가 ('w2grid' --> 'w2grid wq_gvw')
        c_grid.setClass("wq_gvw")

        removeStyleInfo(c_grid, "position")
        removeStyleInfo(c_grid, "top")
        removeStyleInfo(c_grid, "left")
        removeStyleInfo(c_grid, "width")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_grid)

    # content 스타일 정보 삭제
    xf_content_arr = body_root.getElementsByTagName("w2:content")
    xf_content_list = list([getEqElement(t) for t in xf_content_arr])
    for c_content in xf_content_list:
        removeStyleInfo(c_content, "position")
        removeStyleInfo(c_content, "top")
        removeStyleInfo(c_content, "left")
        removeStyleInfo(c_content, "width")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_content)

    # textbox 스타일 정보 삭제
    xf_textbox_arr = body_root.getElementsByTagName("w2:textbox")
    xf_textbox_list = list([getEqElement(t) for t in xf_textbox_arr])
    for c_textbox in xf_textbox_list:
        removeStyleInfo(c_textbox, "position")
        removeStyleInfo(c_textbox, "top")
        removeStyleInfo(c_textbox, "left")
        removeStyleInfo(c_textbox, "width")
        removeStyleInfo(c_textbox, "height")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_textbox)

    # image 스타일 정보 삭제
    xf_image_arr = body_root.getElementsByTagName("xf:image")
    xf_image_list = list([getEqElement(t) for t in xf_image_arr])
    for c_image in xf_image_list:
        removeStyleInfo(c_image, "position")
        removeStyleInfo(c_image, "top")
        removeStyleInfo(c_image, "left")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_image)

    # input 스타일 정보 삭제
    xf_input_arr = body_root.getElementsByTagName("xf:input")
    xf_input_list = list([getEqElement(t) for t in xf_input_arr])
    for c_input in xf_input_list:
        removeStyleInfo(c_input, "position")
        removeStyleInfo(c_input, "top")
        removeStyleInfo(c_input, "left")
        removeStyleInfo(c_input, "height")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_input)

    # trigger 스타일 정보 삭제
    xf_trigger_arr = body_root.getElementsByTagName("xf:trigger")
    xf_trigger_list = list([getEqElement(t) for t in xf_trigger_arr])
    for c_trigger in xf_trigger_list:
        # trigger 버튼에 class 추가 ('w2trigger' --> 'w2trigger btn_cm')
        c_trigger.setClass("btn_cm")

        removeStyleInfo(c_trigger, "width")
        removeStyleInfo(c_trigger, "height")
        removeStyleInfo(c_trigger, "background")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_trigger)

    # select1 스타일 정보 삭제
    xf_select1_arr = body_root.getElementsByTagName("xf:select1")
    xf_select1_list = list([getEqElement(t) for t in xf_select1_arr])
    for c_select1 in xf_select1_list:
        # radio button 인 경우만 width 삭제
        if len(c_select1.allOption) == 0:
            removeStyleInfo(c_select1, "width")
        removeStyleInfo(c_select1, "height")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_select1)

    # select1 스타일 정보 삭제
    xf_select_arr = body_root.getElementsByTagName("xf:select")
    xf_select_list = list([getEqElement(t) for t in xf_select_arr])
    for c_select in xf_select_list:
        removeStyleInfo(c_select, "width")

        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_select)

    # select1 스타일 정보 삭제
    xf_column_arr = body_root.getElementsByTagName("w2:column")
    xf_column_list = list([getEqElement(t) for t in xf_column_arr])
    for c_column in xf_column_list:
        # 기존 style 에서 사용하지 않는 요소를 제거한다.
        remove_style_common(c_column)


"""
    절대좌표 상황에서 group 에 child 가 추가 되는 경우 처리. (절대좌표 → 상대좌표)
    자식 Node 는 left 정렬.
"""


def append_child_element_in_group(g_elem, c_elem):
    g_left, g_top, g_width, g_height = g_elem.left, g_elem.top, g_elem.width, g_elem.height
    c_left, c_top, c_width, c_height = c_elem.left, c_elem.top, c_elem.width, c_elem.height
    c_center_x = c_left + int(c_width / 2)
    c_center_y = c_top + int(c_height / 2)

    # element 절대좌표 top, left 에 해당하는 group 을 찾는다.
    if g_left <= c_center_x <= (g_left + g_width) and g_top < c_center_y < (g_top + g_height):
        # group 에 child 노드를 추가한다. (절대좌표 필요)
        append_eq_child_with_style(g_elem, c_elem)


"""
    body root 를 check 하여 base_group 이 존재하지 않으면 추가.
"""


def check_and_add_base_group(document, body_root):
    # base_group 추가 조건.
    # 1. body_root 에 childNodes 가 1 이고 'group'
    # 2. 그리고 group 의 class 가 'sub_contents' 인 경우 --> base_group 추가.
    if not (len(body_root.childNodes) == 1 and body_root.childNodes[0].localName == "group"
            and getEqElement(body_root.childNodes[0]).class_str == "sub_contents"):

        xf_element_list = []
        childNodes_copy = body_root.childNodes.copy()
        for c in list(childNodes_copy):
            xf_element_list.append(getEqElement(c))
            body_root.removeChild(c)

        # sub_contents group 생성
        g_class = "sub_contents"
        group_0_element = get_new_group(document, g_parent=body_root, g_tyle="", g_class=g_class)

        # group_0_element 에 자식노드를 추가한다.
        for c in xf_element_list:
            group_0_element.element.appendChild(c.element)


"""
    근접한 요소들을 묶어서 하나의 col_members 로 만든다.
"""


def define_col_members(c_elem_row_list):
    # 근접한 col_members 로 묶는다.
    for ii, row in enumerate(c_elem_row_list):

        c_tmp = None

        for jj, c in enumerate(row):

            # col_member 대상으로 "group", "tabControl", "gridView" 제외.
            if c.localName in ["group", "tabControl", "gridView"]:
                continue

            # row 에 textbox 가 없는 경우.
            if c_tmp is None:
                # 자신은 한번만 추가.
                if c not in c.col_members:
                    c.col_members.append(c)
                c_tmp = c

            if jj > 0:

                # column 간격이 threshold 보다 작으면 하나의 column.
                if row[jj - 1].right + config.same_col_threshold > c.left:

                    if c_tmp != c:
                        c_tmp.col_members.append(c)

                # column 간격이 threshold 보다 크면 다른 column.
                elif row[jj - 1].right + config.same_col_threshold < c.left:

                    # c_tmp 업데이트.
                    # 자신은 한번만 추가.
                    if c not in c.col_members:
                        c.col_members.append(c)
                    c_tmp = c


"""
    check count of input style object number
"""


def have_input_style_object(row):
    return_flag = False
    input_obj_cnt = len([c for c in row if c.localName in ["input", "inputcalendar", "select", "select1", "textarea"]])
    if input_obj_cnt > 0:
        return_flag = True

    return return_flag


"""
    Element 의 Style 에 속성을 추가한다.
"""


def addElementStyle(wq_elem, style_string):
    # 원본 element
    elem = wq_elem.element

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):

        # Style 추출
        style_str = elem.attributes.get("style").value.strip().replace(" ", "")
        style_arr = style_str.split(";")

        # 추가하고자 하는 style을 비교하여 추가 또는 삭제한ek.
        style_string_arr = style_string.strip().split(":")
        style_name_param = style_string_arr[0]

        for i, style_elem in enumerate(style_arr):
            if len(style_elem.strip()) == 0:
                continue

            # Element split (['width', '942px'])
            s_elem_arr = style_elem.strip().split(":")
            # style_name ('width')
            style_name = s_elem_arr[0].strip()

            # 기존 style 에 존재하면 삭제.
            if style_name == style_name_param:
                style_arr.remove(style_elem)
                break

            # Style 요소 업데이트
            style_arr[i] = ":".join(s_elem_arr)

        # 입력한 속성이 존재하는 지 체크 후 추가.
        style_name_arr = [s.split(":")[0] for s in style_arr]
        if style_name_param not in style_name_arr:
            style_arr.append(style_string)

        # Style 업데이트
        elem.attributes["style"] = ";".join(style_arr)


"""
    document 와 row 정보를 받아 해당 row 에 group 추가.
    return Eq group element
"""


def get_new_group_for_dfbox(document, row, base_group):
    # dfbox class 정의.
    g_class = "dfbox"

    # 새로운 group 을 생성한다.
    g_elem = get_new_group_with_class(document, row, base_group, g_class)

    # g_elem 반환
    return g_elem


"""
    document 와 row 정보를 받아 해당 row 에 group 추가.
    return Eq group element
"""


def get_new_group_for_lybox(document, row, base_group):
    # lybox class 정의.
    g_class = config.lybox_class

    # 새로운 group 을 생성한다.
    g_elem = get_new_group_with_class(document, row, base_group, g_class)

    # g_elem 반환
    return g_elem


"""
    document 와 row 정보를 받아 해당 row 에 group 추가.
    return Eq group element
"""


def get_new_group_with_class(document, row, base_group, class_str):
    # group element 의 left, top 속성 정의.
    g_top = min([c.top for c in row])

    # 같은 level 의 group element 의 최대 width 를 적용한다.
    # group 이 없는 경우 default 980
    g_width = 980
    # group, tabControl, gridView 목록에서 max_width, min_left 를 구한다.
    # 절대좌표 left 는 group 의 min_left 를 사용한다.
    max_width, min_left = get_max_width_and_min_left(document)
    if max_width > 0:
        g_width = max_width

    # 추가할 group 정의.
    g_style = "position:absolute;left:{}px;top:{}px;width:{}px;" \
        .format(min_left, g_top, g_width)
    g_class = class_str

    # 새로운 group 을 생성한다.
    g_elem = get_new_group(document, g_parent=base_group, g_tyle=g_style, g_class=g_class)

    # g_elem 반환
    return g_elem


"""
    dfbox group 을 생성하고 group 에 child 를 추가한다.
"""


def make_dfbox_group_and_arrange_child(document, base_group, c_elem_row_list):
    for i, row in enumerate(c_elem_row_list):

        if len(row) > 0:

            # row 단위로 dfbox 조건에 맞는지 체크.
            if is_dfbox_group_for_row(row):
                # dfbox group 을 구성한다.
                make_dfbox_group(document, row, base_group, g_elem_param=None)


"""
    dfbox group 대상인지 확인.
    1. 한 줄 group 이고.
    2. "gridView", "input", "select1", "select" 등이 없으며 True 를 반환.
"""


def is_dfbox_group(c_elem_row_list):
    dfbox_flag = False

    # "gridView", "input", "select1", "select" 등이 포함된 count.
    input_elem_obj_cnt = len([c for c in c_elem_row_list[0] if c.localName
                              in ["gridView", "tabControl", "input", "select1", "select"]])

    # width 가 700px 이상인 group count.
    group_width_check_cnt = len([c for c in c_elem_row_list[0] if
                                 c.localName == "group" and not is_hidden(c) and c.width > config.min_group_width])

    # hidden 을 제외한 count
    except_hidden_cnt = len([c for c in c_elem_row_list[0] if not is_hidden(getEqElement(c))])

    # 1. 한 줄 group 이고.
    # 2. input_elem_obj_cnt 가 0 이면.
    # 3. hidden 항목을 제외한 개수가 0 보다 크면.
    if len(c_elem_row_list) == 1 and input_elem_obj_cnt == 0 and group_width_check_cnt == 0 and except_hidden_cnt > 0:
        dfbox_flag = True

    return dfbox_flag


"""
    dfbox group 대상인지 확인.
    1. 한 줄 group 이고.
    2. "gridView", "input", "select1", "select" 등이 없으며 True 를 반환.
"""


def is_dfbox_group_for_row(row):
    dfbox_flag = False

    # group 이 하나만 존재하고 width 가 700 px 보다 크면 dfbox 를 적용하지 않는다.
    if len(row) == 1 and row[0].localName == "group" and row[0].width > config.min_group_width:
        return dfbox_flag

    # group component 의 타 class 제외
    group_component_cnt = len(
        [c for c in row if c.localName == "group" and c.class_str in ["tabbox", "tvwbox", "gvwbox", "lybox"]])

    # group width 가 700px 이상 존재 체크.
    group_width_check_cnt = len([c for c in row if c.localName == "group" and c.width > config.min_group_width])

    # "gridView", "input", "select1", "select" 등이 포함된 count.
    input_elem_obj_cnt = len([c for c in row if c.localName
                              in ["gridView", "tabControl", "treeView", "input", "select1", "select"]])

    # hidden 을 제외한 count
    except_hidden_cnt = len([c for c in row if not is_hidden(getEqElement(c))])

    # 1. input_elem_obj_cnt 가 0 이면.
    # 2. hidden 항목을 제외한 개수가 0 보다 크면.
    if group_component_cnt == 0 and group_width_check_cnt == 0 and input_elem_obj_cnt == 0 and except_hidden_cnt > 0:
        dfbox_flag = True

    return dfbox_flag


"""
    dfbox group 을 구성한다.
"""


def make_dfbox_group(document, row, base_group, g_elem_param=None):
    # row 에 'group' 이 존재하는 지 확인.
    if len([c for c in row if c.localName in ["group", "tabControl", "gridView"]]) > 0:

        # group 이 2 개의 경우.
        if len([c for c in row if c.localName == "group" and len(c.element.childNodes) > 0]) == 2:

            # g_elem 을 입력 받는 경우.
            if g_elem_param:
                g_elem = g_elem_param
            else:
                # dfbox group 추가.
                g_elem = get_new_group_for_dfbox(document, row, base_group)

            group_arr = [c for c in row if c.localName == "group" and len(c.element.childNodes) > 0]
            group_fl = group_arr[0]
            group_fr = group_arr[1]

            group_fl.element.setAttribute("class", "{}".format("fl"))
            group_fr.element.setAttribute("class", "{}".format("fr"))

            # base_group 에서 부모-자식 관계를 remove.
            group_fl.element.parentNode.removeChild(group_fl.element)
            group_fr.element.parentNode.removeChild(group_fr.element)

            # base_group 에 group_fl, group_fr 추가.
            g_elem.element.appendChild(group_fl.element)
            g_elem.element.appendChild(group_fr.element)

        # group 이 1 개의 경우.
        elif len([c for c in row if c.localName == "group" and len(c.element.childNodes) > 0]) == 1 and \
                [c for c in row if c.localName == "group" and len(c.element.childNodes) > 0][0].width < 700:

            group_fl = None
            group_fr = None

            # g_elem 을 입력 받는 경우.
            if g_elem_param:
                g_elem = g_elem_param
            else:
                # dfbox group 추가.
                g_elem = get_new_group_for_dfbox(document, row, base_group)

            # group array 구성.
            group_arr = [c for c in row if c.localName == "group" and len(c.element.childNodes) > 0]

            # 중앙선을 넘는 group 이 존재하면.
            if len(list([c for c in row if c.localName == "group" and len(c.element.childNodes) > 0
                                           and int((c.left + c.right) / 2) > int(
                config.DEFAULT_SCREEN_WIDTH / 2)])) > 0:
                # fr
                group_fr = group_arr[0]
                # fl
                left_or_right = "fl"
                group_fl = None
            else:
                # fl
                group_fl = group_arr[0]
                # fr
                left_or_right = "fr"
                group_fr = None

            # work group 추가
            # 부모 group 속성 추가
            group_element_c = getEqElement(document.createElement("xf:group"))
            group_element_c.element.setAttribute("class", "{}".format(left_or_right))
            g_elem.element.appendChild(group_element_c.element)

            # group 을 제외한 자식 목록 추가.
            for c_elem_2 in list([c for c in row if c.localName != "group"]):
                # group element 에 자식노드 추가
                if c_elem_2.element.parentNode:
                    c_elem_2.element.parentNode.removeChild(c_elem_2.element)
                group_element_c.element.appendChild(c_elem_2.element)

            if group_fr is None:
                group_fr = group_element_c
            else:
                group_fl = group_element_c

            group_fl.element.setAttribute("class", "{}".format("fl"))
            group_fr.element.setAttribute("class", "{}".format("fr"))

            # base_group 에서 부모-자식 관계를 remove.
            group_fl.element.parentNode.removeChild(group_fl.element)
            group_fr.element.parentNode.removeChild(group_fr.element)

            # base_group 에 group_fl, group_fr 추가.
            g_elem.element.appendChild(group_fl.element)
            g_elem.element.appendChild(group_fr.element)

        # group 이 1 개의 경우.
        # 일반적인 경우로 group (width 700 이상) 에 child 를 추가한다.
        elif len([c for c in row if c.localName == "group" and len(c.element.childNodes) > 0]) == 1 and \
                [c for c in row if c.localName == "group" and len(c.element.childNodes) > 0][0].width >= 700:

            g_elem = [c for c in row if c.localName == "group" and len(c.element.childNodes) > 0][0]

            # g_elem 을 입력 받는 경우.
            if g_elem_param:
                g_elem = g_elem_param

            for j, c_elem in enumerate(row):

                if c_elem.localName == "group":
                    continue

                if g_elem is not None:
                    # group 에 child 추가 하면서 child 노드 절대좌표 수정.
                    append_child_element_in_group(g_elem, c_elem)

                # 마지막 child 에 도달하면 g_elem 초기화.
                if c_elem == row[-1]:
                    g_elem = None

    # Group element 가 존재하지 않으므로 group 을 생성하고 추가한다.
    else:

        # g_elem 을 입력 받는 경우.
        if g_elem_param:
            g_elem = g_elem_param
        else:
            # document 와 row 정보를 받아 해당 row 에 group 추가.
            g_elem = get_new_group_for_dfbox(document, row, base_group)

        # col_members 목록 임시 저장소
        tmp_col_members = []

        # group 과 자식 element 의 관계 설정.
        # 자식 Node 는 left 정렬.
        for j, c_elem in enumerate(row):
            # group 에 child 추가 하면서 child 노드 절대좌표 수정.
            append_child_element_in_group(g_elem, c_elem)

        # group 과 자식 element 의 관계 설정.
        for j, c_elem in enumerate(row):

            # 자식 element 중에 col_members 를 가진 경우.
            if len(c_elem.col_members) > 0:

                # 임시 col_members 세팅.
                tmp_col_members = c_elem.col_members

                # 화면 가운데를 기준으로 기준폭보다 왼쪽이면 left
                # 화면 가운데를 기준으로 기준폭보다 오른쪽이면 right
                left_or_right = ""
                if (c_elem.left + c_elem.right) / 2 <= int(config.DEFAULT_SCREEN_WIDTH / 2):
                    left_or_right = "fl"
                elif (c_elem.left + c_elem.right) / 2 > int(config.DEFAULT_SCREEN_WIDTH / 2):
                    left_or_right = "fr"

                # work group 추가
                # 부모 group 속성 추가
                group_element_c = getEqElement(document.createElement("xf:group"))
                group_element_c.element.setAttribute("class", "{}".format(left_or_right))
                g_elem.element.appendChild(group_element_c.element)

                for c_elem_2 in tmp_col_members:
                    # group element 에 자식노드 추가
                    if c_elem_2.element.parentNode:
                        c_elem_2.element.parentNode.removeChild(c_elem_2.element)
                    group_element_c.element.appendChild(c_elem_2.element)

            # 마지막 row 에서 group element 초기화.
            if c_elem == row[-1]:
                g_elem = None

    # group 처리 후 절대좌표 정보로 정렬.
    if len(base_group.childNodes) > 0:
        re_arrange_elements(base_group)


"""
    Node 검색 및 position 정보 제거.
"""


def search_and_remove_position_info(node):
    # 1. 자식 Node 가 존재하고.
    # 2. localName 이 "gridView", "tabControl", "trigger", "select", "select1" 가 아니면.
    # (즉, 자식 node 가 존재하지만 최종 node 에 해당하는 경우 제외.)
    if len(node.childNodes) > 0 and (node.localName not in config.localname_last_node_arr):

        # position 정보인 top, left 정보를 제거한다.
        remove_postion_info(node)

        # Node 검색
        for child in node.childNodes:
            # search child nodes
            search_and_remove_position_info(child)


"""
    부모 객체에 대해서.
    모든 component 에서 position 정보인 left, top 을 제거한다.
"""


def remove_postion_info(elem):
    # Parent Node 판단.
    if len(elem.childNodes) > 0:

        wq_elem_list = []

        # minidom childnodes loop
        for e in list(elem.childNodes):

            # Element Node 만 추가
            if e.nodeType == config.ELEMENT_NODE:
                # EqElement를 만든다.
                wq_elem_list.append(getEqElement(e))

        # 정렬을 마친 후 일괄적으로 position 의 left, top 정보를 제거한다.
        for wq_e in wq_elem_list:
            # position, top, left 정보 제거.
            removeStyleInfo(wq_e, "position")
            removeStyleInfo(wq_e, "left")
            removeStyleInfo(wq_e, "top")


"""
    동일 Level 에 존재하는 group 과 기타 object 들의 관계를 재설정.
    gridView 등이 좌표상 group 에 포함이 되도록 실행.
"""


def rearrange_siblings_by_coordinate(node):
    g_elem = getEqElement(node)
    g_left, g_top, g_width, g_height = g_elem.left, g_elem.top, g_elem.width, g_elem.height

    childNodes_copy = node.parentNode.childNodes.copy()
    for i, c in enumerate(childNodes_copy):
        c_elem = getEqElement(c)

        # 자기 자신 제외한 siblings 처리.
        if c == node:
            continue

        # left, top 세팅.
        c_left, c_top, c_width, c_height = c_elem.left, c_elem.top, c_elem.width, c_elem.height
        c_center_x = c_left + int(c_width / 2)
        c_center_y = c_top + int(c_height / 2)

        # element 절대좌표 top, left 에 해당하는 group 을 찾는다.
        if g_left < c_center_x < (g_left + g_width) and g_top < c_center_y < (g_top + g_height):
            # group 에 child 노드를 추가한다. (절대좌표 필요)
            append_eq_child_with_style(g_elem, c_elem)


"""
    hidden 판단.
"""


def is_hidden(elem):
    hidden_val = False
    if elem.display == "none" or elem.visibility == "hidden":
        hidden_val = True
    return hidden_val


"""
    group 에 child 노드를 추가한다.
"""


def append_eq_child_with_style(g_elem, c_elem):
    # parentNode 가 존재하는 경우만 실행.
    if c_elem.element.parentNode is not None:
        # 기존 부모/자식 관계를 끊는다.
        c_elem.element.parentNode.removeChild(c_elem.element)

        # 좌표에 해당하는 group 에 추가한다.
        g_elem.element.appendChild(c_elem.element)

        # group re_arrange by left and top
        re_arrange_elements(g_elem.element)

        # Element 의 Style 을 업데이트 한다.
        update_position_info(c_elem, g_elem)


"""
    Write success log
"""


def write_log_success(log_file_root, log_file_name, source_xml_file_name, result_xml_file_name, curr_yyyymmddhhmiss,
                      log_message):
    f = open('{}/{}'.format(log_file_root, log_file_name), 'a')
    f.write("[{}][{}][{}][success][{}]\n".format(curr_yyyymmddhhmiss, source_xml_file_name.split("/")[-1],
                                                 result_xml_file_name.split("/")[-1], log_message))
    f.close()


"""
    Write error log
"""


def write_log_error(log_file_root, log_file_name, source_xml_file_name, result_xml_file_name, curr_yyyymmddhhmiss,
                    log_message):
    f = open('{}/{}'.format(log_file_root, log_file_name), 'a')
    f.write("[{}][{}][{}][error][{}]\n".format(curr_yyyymmddhhmiss, source_xml_file_name.split("/")[-1],
                                               result_xml_file_name.split("/")[-1], log_message))
    f.close()


"""
    log file name 구성 (파일)
"""


def get_log_file_name_with_file(file_name):
    curr_yyyymmddhhmiss = get_curr_date_yyyymmddhhmmss()
    curr_yyyymmdd_hhmiss = "{}_{}".format(curr_yyyymmddhhmiss[:8], curr_yyyymmddhhmiss[8:])

    # Windows 파일 경로가 존재하는 경우 대응.
    file_name = "/".join(file_name.split("\\"))
    # 경로와 file명 분리
    log_file_root = "/".join(file_name.split("/")[:-1])
    last_file_name = file_name.split("/")[-1]

    # log 파일명
    log_file_name = "{}_{}.log".format(curr_yyyymmdd_hhmiss, last_file_name)

    return log_file_root, log_file_name, curr_yyyymmddhhmiss


"""
    log file name 구성 (폴더)
"""


def get_log_file_name_with_folder(dir_path):
    curr_yyyymmddhhmiss = get_curr_date_yyyymmddhhmmss()
    curr_yyyymmdd_hhmiss = "{}_{}".format(curr_yyyymmddhhmiss[:8], curr_yyyymmddhhmiss[8:])

    # Windows 파일 경로가 존재하는 경우 대응.
    file_path = "/".join(dir_path.split("\\"))
    # 경로와 file명 분리
    log_file_root = "/".join(file_path.split("/"))
    last_folder_name = file_path.split("/")[-1]

    # log 파일명
    log_file_name = "{}_{}.log".format(curr_yyyymmdd_hhmiss, last_folder_name)

    return log_file_root, log_file_name, curr_yyyymmddhhmiss


"""
    절대좌표의 position 정보가 존재하는 지 체크한다.
"""


def is_absolute(elem):
    # position 정보가 존재하면 True.
    absolute_flag = False

    # attributes 가 존재하면.
    if elem.attributes and elem.attributes.get("style"):
        style_str = elem.attributes.get("style").value.strip()

        # Style 추출
        style_arr = style_str.split(";")

        # absolute 의 경우만 적용.
        if "position:absolute" in style_arr:
            absolute_flag = True

    return absolute_flag


"""
    group 에 배열 형태의 child 를 추가한다. (절대좌표 수정 없음)
"""


def append_child_element_by_array(group_table_c, row_list):
    for row in row_list:
        # row 의 Iterable 체크.
        if not isinstance(row, Iterable):
            group_table_c.element.appendChild(row.element)

        elif len(row) > 1:
            # Table row 구성
            for c in row:
                group_table_c.element.appendChild(c.element)


"""
    table group 상위에 table class group 으로 한 번 감싼다.
"""


def wrap_group_table(document, group_table):
    # 부모 group 이 lybox 이면 ly_column 을 추가한다.
    parent_elem = getEqElement(group_table.element.parentNode)
    if parent_elem.class_str == config.lybox_class and group_table.class_str == config.lycolumn_class:
        # table group 상위에 table class group 으로 한 번 감싼다.
        wrap_by_group_with_class(document, group_table, config.lycolumn_class)

    # table group 상위에 table class group 으로 한 번 감싼다.
    wrap_by_group_with_class(document, group_table, config.tbl_class)


"""
    특정 class 의 group 으로 감싼다.
"""


def wrap_by_group_with_class(document, group_table, group_class):
    # group 의 parent 노드를 가져온다.
    group_tbl_parent = group_table.element.parentNode

    # siblings 를 저장할 array.
    child_siblings = []
    # 해당 group 의 index.
    self_index = 0
    # group table 자식들을 순서대로 array 에 저장.
    for i, c in enumerate(group_tbl_parent.childNodes):
        child_siblings.append(c)
        # 해당 group table 의 index.
        if c == group_table.element:
            self_index = i

    # 부모-자식 관계 제거.
    group_tbl_parent.removeChild(group_table.element)

    # group row 생성
    group_tbl = document.createElement("xf:group")
    group_tbl.setAttribute("class", group_class)
    group_tbl.appendChild(group_table.element)

    # 새로 생성한 group 객체에 부모-자식 관계 설정.
    group_tbl_parent.appendChild(group_tbl)

    # array 목록에서 제거.
    child_siblings.pop(self_index)
    # 해당 group table 을 self_index 위치에 추가.
    child_siblings.insert(self_index, group_tbl)

    # Loop 돌면서 array 에 저장된 순서로 재배치.
    if len(child_siblings) > 0:
        for c in child_siblings:
            group_tbl_parent.removeChild(c)
            group_tbl_parent.appendChild(c)


"""
    특정 class 의 group 으로 감싼다.
"""


def insert_child_group_with_class(document, group_table, group_class):
    # siblings 를 저장할 array.
    child_siblings = []
    # group table 자식들을 순서대로 array 에 저장.
    for i, c in enumerate(group_table.childNodes):
        child_siblings.append(c)

    # group row 생성
    group_tbl_new = document.createElement("xf:group")
    group_tbl_new.setAttribute("class", group_class)
    group_table.appendChild(group_tbl_new)

    # Loop 돌면서 array 에 저장된 순서로 재배치.
    if len(child_siblings) > 0:
        for c in child_siblings:
            group_table.removeChild(c)
            group_tbl_new.appendChild(c)


"""
    Row 단위로 gridView, tabControl, treeView 에 대해서 class 지정과 함께 상위 group 추가.
"""


def add_class_to_group_component(document, body_root):
    base_group = body_root.childNodes[0]

    # Group element 의 wq element child list 를 만든다.
    c_elem_list = [getEqElement(c) for c in base_group.childNodes]

    # make table row list
    c_elem_row_list = make_row_list(c_elem_list)

    # group component (gridView, tabControl, treeView) 별로 class 를 적용한다.
    for row in c_elem_row_list:

        for c in row:

            # gridView 처리.
            if c.localName == "gridView" and not is_hidden(c):

                # 부모 노드
                p_elem = getEqElement(c.element.parentNode)

                # hidden 이 아니고 gvwbox class 가 아니면.
                if p_elem.class_str != config.gvw_class:
                    # group component 별로 class 를 적용한다.
                    rearrange_siblings_with_class_group(document, base_group, row, c, config.gvw_class)

            # tabControl 처리.
            elif c.localName == "tabControl" and not is_hidden(c):

                # 부모 노드
                p_elem = getEqElement(c.element.parentNode)

                # 자식 노드
                c_elem_list = [getEqElement(x) for x in c.element.childNodes]

                # 자식 노드에 반드시 tabs 노드가 존재해야 함.
                if len(c_elem_list) > 0:
                    if p_elem.class_str != config.tab_class and c_elem_list[0].localName == "tabs":
                        # group component 별로 class 를 적용한다.
                        rearrange_siblings_with_class_group(document, base_group, row, c, config.tab_class)

            # treeView 처리.
            elif c.localName == "treeView" and not is_hidden(c):

                # 부모 노드
                p_elem = getEqElement(c.element.parentNode)

                if p_elem.class_str != config.tvw_class:
                    # group component 별로 class 를 적용한다.
                    rearrange_siblings_with_class_group(document, base_group, row, c, config.tvw_class)

    w2_gridView_list = [getEqElement(c) for c in document.getElementsByTagName("w2:gridView")]
    w2_tabControl_list = [getEqElement(c) for c in document.getElementsByTagName("w2:tabControl")]
    w2_treeView_list = [getEqElement(c) for c in document.getElementsByTagName("w2:treeView")]

    for c in w2_gridView_list:
        if c.localName == "gridView" and not is_hidden(c):
            p = getEqElement(c.element.parentNode)
            if p.class_str != config.gvw_class:
                # component (EQ element) 상위에 table class group 으로 한 번 감싼다.
                wrap_by_group_with_class(document, c, config.gvw_class)

    for c in w2_tabControl_list:
        if c.localName == "tabControl" and not is_hidden(c):
            p = getEqElement(c.element.parentNode)
            if p.class_str != config.tab_class:
                # component (EQ element) 상위에 table class group 으로 한 번 감싼다.
                wrap_by_group_with_class(document, c, config.tab_class)

            # tabControl 의 구성요소(tabs, content)를 각각 id 정렬 후 tabs, content 별로 구성한다.
            restruct_tabs_and_sort_by_id(c, [getEqElement(x) for x in c.element.childNodes])

    for c in w2_treeView_list:
        if c.localName == "treeView" and not is_hidden(c):
            p = getEqElement(c.element.parentNode)
            if p.class_str != config.tvw_class:
                # component (EQ element) 상위에 table class group 으로 한 번 감싼다.
                wrap_by_group_with_class(document, c, config.tvw_class)


"""
    Eq element 리스트를 입력받아 해당 행이 lybox 대상인지 구분한다.
"""


def is_lybox(row):
    # lybox_flag 설정
    lybox_flag = False

    # lybox 여부 체크 (group 의 개수 체크)
    # group 이 2 개인 경우 lybox 대상.
    if len([c for c in row if c.localName == "group" and not is_hidden(c)]) == 2:

        # group 의 자식 node 중에
        for c_elem in row:

            # group 이면서 자식 node 에
            # gridView, tabControl, treeView
            # input, select, select1, calendar 항목이 있는지 체크한다.
            if c_elem.localName == "group":
                childNodes_copy = c_elem.element.childNodes.copy()

                for cc in childNodes_copy:
                    cc_elem = getEqElement(cc)

                    # gridView, tabControl, treeView / input, select, select1, calendar 등이 존재하면.
                    # lybox 로 판단한다.
                    if cc_elem.localName \
                            in ["gridView", "tabControl", "treeView", "input", "select", "select1", "calendar"] \
                            and not is_hidden(cc_elem):
                        # lybox_flag 설정
                        lybox_flag = True
                        break

    return lybox_flag


"""
    lybox 대상을 찾아 재구성. (class 재설정, lybox, ly_column)
"""


def find_lybox_and_restruct(document, body_root):
    base_group = body_root.childNodes[0]

    # Group element 의 wq element child list 를 만든다.
    c_elem_list = sorted([getEqElement(c) for c in base_group.childNodes], key=lambda x: (x.top, x.left))

    # 01. make table row list
    c_elem_row_list = make_row_list(c_elem_list)

    # lybox 여부를 판단하여 lybox 로 재구성한다.
    for i, row in enumerate(c_elem_row_list):

        # lybox 여부를 판단하여 lybox 재구성.
        if is_lybox(row):

            # lybox group 생성.
            g_elem = get_new_group_for_lybox(document, row, base_group)

            # group list copy 본
            g_list_copy = [c for c in row if c.localName == "group" and not is_hidden(c)].copy()

            for c in g_list_copy:
                # 관계 제거.
                c.element.parentNode.removeChild(c.element)

                # 자식 node 추가.
                c.setClass(config.lycolumn_class)
                g_elem.element.appendChild(c.element)

                # group 재구성
                restruct_group(document, c)


"""
    row 배열에서 component 를 포함하는 group 이 존재하는 지 체크.
"""


def has_one_group_with_component(c_elem_row_list):
    group_flag = False

    # group 이 1 개인지 체크.
    if len([c for c in c_elem_row_list if c.localName == "group" and not is_hidden(c)]) == 1:

        # group 의 자식 node 중에
        for c_elem in c_elem_row_list:

            # group 이면서 자식 node 에
            # input, select, select1, calendar 항목이 있는지 체크한다.
            if c_elem.localName == "group":
                c_child_copy = c_elem.element.childNodes.copy()

                for cc in c_child_copy:
                    cc_elem = getEqElement(cc)

                    # gridView, tabControl, treeView / input, select, select1, calendar 등이 존재하면.
                    # lybox 로 판단한다.
                    if cc_elem.localName in ["input", "select", "select1", "calendar"]:
                        # group_flag 설정
                        group_flag = True
                        break

    return group_flag


"""
    group component 별로 class 를 적용한다.
"""


def rearrange_siblings_with_class_group(document, base_group, row, c, class_str):
    # child 목록 구성.
    childNodes_list = []

    # child 목록 copy본
    childNodes_copy = c.element.parentNode.childNodes.copy()

    # child 목록을 순차적으로 삭제 및 추가 하기위한 목록을 구성한다.
    for cc in childNodes_copy:
        if cc == c.element:
            # append 노드
            new_group = get_new_group_with_class(document, row, base_group, class_str)
            new_group.element.appendChild(c.element)
            # cc 세팅.
            cc = new_group.element

        # child 목록
        childNodes_list.append(cc)

    # child 목록을 순차적으로 삭제 및 추가.
    for cc in childNodes_list:
        p = cc.parentNode
        if cc.parentNode:
            p.removeChild(cc)
            p.appendChild(cc)


"""
    기존 group 의 class 를 체크하여 group 을 추가 또는 수정한다.
    check_classes : check_classes 에 해당하는 경우 group 을 추가한다.
                    es> ["lybox", "ly_column"]
"""


def insert_or_set_group_class(document, group_table_c, check_classes, group_class):
    # group 에 기존 setting 된 class 가 존재하는 경우 하위에 group 추가.
    if group_table_c.class_str in check_classes:
        insert_child_group_with_class(document, group_table_c.element, group_class)
    else:
        group_table_c.setClass(group_class)


"""
    tabControl 의 content 에 group 이 없는 경우 추가.
"""


def add_group_to_tab_content_child(document):
    # tabControl 의 content 에 group 이 없는 경우 추가.
    w2_content_arr = document.getElementsByTagName("w2:content")
    for c_content in w2_content_arr:
        childNodes_copy = c_content.childNodes.copy()
        if len(childNodes_copy) > 0:

            # child 노드의 첫번째가 group 이 아닌 경우 추가.
            if getEqElement(childNodes_copy[0]).localName != "group":
                insert_child_group_with_class(document, c_content, "")
                c_content.childNodes[0].setAttribute("style", "width:{}px;".format(config.min_group_width))

            # tabControl 의 content 내에서 dfbox 를 찾아 생성한다.
            find_and_make_dfbox_of_content(document, c_content)


"""
    group 의 child 노드 중에 width 400px 넘는 것이 있으면 table 변환하지 않는다.
"""


def has_large_group(c_elem_row_list):
    # return value
    has_flag = False

    # TODO : 삭제
    """
    # child 노드 중에 width 400px 넘는 것이 있는 지 체크.
    childNodes_copy = group_table.element.childNodes.copy()
    for c in list(childNodes_copy):
        # group 이고 width 가 400px 넘는 지 체크.
        c_elem = getEqElement(c)
        if c_elem.localName == "group" and c_elem.width >= int(config.min_group_width/2):
            has_flag = True
            break
    """

    # c_elem_row_list 의 길이가 1인 것만 대상으로 한다.
    # child 노드 중에 width 400px 넘는 것이 있는 지 체크.
    if len(c_elem_row_list) == 1:
        for row in c_elem_row_list:
            for c_elem in row:
                # group 이고 width 가 400px 넘는 지 체크.
                if c_elem.localName == "group" and c_elem.width >= int(config.min_group_width / 2):
                    has_flag = True

                    # parentNode 저장
                    parentNode = c_elem.element.parentNode

                    # 정렬 순서를 위해서 부모의 관계를 끊고 다시 연결한다.
                    parentNode.removeChild(c_elem.element)
                    parentNode.appendChild(c_elem.element)

                    break

    return has_flag


"""
    find group by control_id
"""


# TODO : 삭제 (테스트용)
def find_group_by_control_id(body_root, control_id):
    ret_group = None
    xf_group_list = get_xf_group_list(body_root)
    for g in xf_group_list:
        if g.control_id == control_id:
            ret_group = g
            break
    return ret_group


"""
    tabControl 의 content 내에서 dfbox 를 찾아 생성한다.
"""


def find_and_make_dfbox_of_content(document, base_group):
    # Group element 의 wq element child list 를 만든다.
    c_elem_list = [getEqElement(c) for c in base_group.childNodes]

    # 01. make table row list
    c_elem_row_list = make_row_list(c_elem_list)

    # 근접한 요소들을 묶어서 하나의 col_members 로 만든다.
    define_col_members(c_elem_row_list)

    # dfbox group 을 생성하고 group 에 child 를 추가한다.
    make_dfbox_group_and_arrange_child(document, base_group, c_elem_row_list)


"""
    기존 style 에서 사용하지 않는 요소를 제거한다.
"""


def remove_style_common(wq_elem):
    # background-color, border-color, border, color, font-family, font-size, text-align, overflow 정보 제거.
    removeStyleInfo(wq_elem, "background-color")
    removeStyleInfo(wq_elem, "border-color")
    removeStyleInfo(wq_elem, "border")
    removeStyleInfo(wq_elem, "color")
    removeStyleInfo(wq_elem, "font-family")
    removeStyleInfo(wq_elem, "font-size")
    removeStyleInfo(wq_elem, "text-align")
    removeStyleInfo(wq_elem, "overflow")


"""
    문자열을 split 하여 첫번째 return
"""


def get_first(str_content, str_seperator):
    return_first = ""
    str_arr = str_content.split(str_seperator)
    if len(str_arr) > 1:
        return_first = str_arr[0].strip()

    return return_first


"""
    col span, row span attributes 추가
"""


def add_span_attributes(document, th_td_el):
    # attributes 객체 생성
    w2_attributes = document.createElement("w2:attributes")

    # create colspan
    w2_colspan = document.createElement("w2:colspan")
    text_col_span = document.createTextNode(str(th_td_el.col_span))
    w2_colspan.appendChild(text_col_span)

    # create rowspan
    w2_rowspan = document.createElement("w2:rowspan")
    text_row_span = document.createTextNode(str(1))
    w2_rowspan.appendChild(text_row_span)

    # attributes 구성
    w2_attributes.appendChild(w2_colspan)
    w2_attributes.appendChild(w2_rowspan)

    # text node child 추가
    th_td_el.element.appendChild(w2_attributes)


"""
    tabControl 의 구성요소를 id 정렬 후 tabs, content 별로 구성한다.
"""


def restruct_tabs_and_sort_by_id(c, c_elem_child_list):
    # tabs, content 별로 모아서 id 로 정렬한다.
    tabs_list = []
    content_list = []
    for c_elem in c_elem_child_list:
        if c_elem.localName == "tabs":
            tabs_list.append(c_elem)
        elif c_elem.localName == "content":
            content_list.append(c_elem)

    # 자식 node 삭제.
    childNodes_copy = c.element.childNodes.copy()
    for c_tc in childNodes_copy:
        c.element.removeChild(c_tc)

    # tabs node 재구성.
    tabs_list.sort(key=lambda x: x.id_index)
    for c_t in tabs_list:
        c.element.appendChild(c_t.element)

    # content node 재구성.
    content_list.sort(key=lambda x: x.id_index)
    for c_c in content_list:
        c.element.appendChild(c_c.element)


"""
    문자열 + 숫자 조합에서 숫자만 추출한다.
"""


def get_digit(str_value):
    ret_num = "0"
    str_num = re.sub(r'[^0-9]', '', str_value)
    if len(str_num) > 0:
        ret_num = str_num
    return ret_num


"""
    자식 node 가 하나이고 group 이면 제거한다.
"""


def search_and_remove_surplus_child_group(group_table):

    # base_group 제외.
    # 자식 node 가 group 이면서 하나이면
    # 그리고 자식 node 를 가지며
    # 자식 node 의 id 값이 "" 이면 삭제한다.
    if group_table.class_str != "sub_contents" \
            and len(group_table.element.childNodes) == 1 \
            and getEqElement(group_table.element.childNodes[0]).localName == "group" \
            and len(group_table.element.childNodes[0].childNodes) > 1 \
            and len(getEqElement(group_table.element.childNodes[0]).id) == 0:

        # 자식의 자식 node 를 가져와서 copy 한다.
        childNodes_copy = group_table.element.childNodes[0].childNodes.copy()
        for c in childNodes_copy:
            group_table.element.childNodes[0].removeChild(c)
            group_table.element.appendChild(c)

        # 부모 group 에서 자식 node 제거.
        group_table.element.removeChild(group_table.element.childNodes[0])

        # 자식 node 가 하나이고 group 이면 제거한다.
        # 재귀호출
        search_and_remove_surplus_child_group(group_table)


"""
    div_table 구조인지 체크하고 group 을 div_table 로 구성한다.
"""


def is_div_table(row):
    # div_table 설정
    div_table_flag = False

    for c in row:

        # group 만 체크
        # 최소 group width 보다 크면, div_table 대상이다.
        # 자식 node 중에 div_table 대상을 조회한다.
        if c.localName == "group" and c.width > config.min_group_width:
            # 자식 node 중에 group 이 존재하는 지 체크.
            childNodes = c.element.childNodes
            childNodes_group = [x for x in childNodes if getEqElement(x).localName == "group"]
            if len(childNodes) > 0 and len(childNodes_group) > 0:

                for cc in c.element.childNodes:
                    if getEqElement(cc).localName == "group":

                        for ccc in cc.childNodes:
                            if getEqElement(ccc).localName == "group":

                                childNodes_ccc_input = [getEqElement(x) for x in ccc.childNodes if
                                                        getEqElement(x).localName in config.localname_last_node_arr]
                                # 자식 node 중에 입력 항목이 존재하는 지 체크하고 존재하면 div_table 로 구성.
                                if len(childNodes_ccc_input) > 0:
                                    div_table_flag = True
                                    break

    return div_table_flag


"""
    div_table 구조를 찾아 재구성한다.
"""


def find_div_table_and_restruct(document, body_root):
    base_group = body_root.childNodes[0]

    # Group element 의 wq element child list 를 만든다.
    c_elem_list = sorted([getEqElement(c) for c in base_group.childNodes], key=lambda x: (x.top, x.left))

    # 01. make table row list
    c_elem_row_list = make_row_list(c_elem_list)

    # lybox 여부를 판단하여 lybox 로 재구성한다.
    for i, row in enumerate(c_elem_row_list):

        # group 이 존재하고
        # group > group > group 의 자식 node 가 존재하고 input 항목이 하나라도 존재하면 div_table 로 구성한다.
        if is_div_table(row):

            for c_group in row:

                # sub_contents 하위의 group
                if c_group.localName == "group" and c_group.id == "tabInput":

                    # group 에 class 추가.
                    c_group.setClass("div_table")

                    # Group element 의 wq element child list 를 만든다.
                    c_elem_list = [getEqElement(x) for x in c_group.element.childNodes]

                    # make table row list
                    c_elem_row_list = make_row_list(c_elem_list)

                    # th, td node 를 정의한다.
                    define_th_td_node(c_elem_row_list)

                    # items group 을 만들기 위한 목록
                    group_box = []
                    # items 리스트
                    group_items_list = []

                    for row in c_elem_row_list:

                        for cx in row:

                            # group 이 아닌 경우.
                            if cx.localName != "group":

                                # th 에 해당하는 column 을 저장한다.
                                if cx.col_type == "th" and len(cx.col_members) > 0:
                                    group_box = cx.col_members

                                elif cx.col_type == "td":
                                    group_box.extend(cx.col_members)

                                    # group 으로 묶는다.
                                    if len(group_box) > 0:

                                        g_new = document.createElement("xf:group")
                                        g_new.setAttribute("class", "items")

                                        # 부모/자식 관계 설정
                                        for c_tmp in group_box:

                                            if c_tmp.localName != "group":
                                                # 부모/자식 관계 설정
                                                c_tmp.element.parentNode.removeChild(c_tmp.element)
                                                g_new.appendChild(c_tmp.element)

                                            elif c_tmp.localName == "group":
                                                # class 설정.
                                                c_tmp.setClass("items")
                                                # 부모/자식 관계 설정
                                                c_tmp.element.parentNode.removeChild(c_tmp.element)
                                                # items group 목록에 추가.
                                                group_items_list.append(c_tmp.element)

                                                # 만약 이 group 이 마지막이 아니면, 새로운 group 추가.
                                                if c_tmp != group_box[-1]:
                                                    g_new = document.createElement("xf:group")
                                                    g_new.setAttribute("class", "items")

                                                # group 인 경우 자식에 존재하는 group 리스트에서 첫번째를 제외하고 hidden 처리한다.
                                                childNodes_items = c_tmp.element.childNodes
                                                for ii, g_item in enumerate(childNodes_items):

                                                    # 첫번째 제외. (items group 인 것만 대상으로 한다.)
                                                    if ii > 0 and getEqElement(g_item).localName == "group":
                                                        style_string = "display: none;"
                                                        addElementStyle(getEqElement(g_item), style_string)

                                        # items group 목록에 추가.
                                        group_items_list.append(g_new)

                                    # group_box 초기화. (목록 저장 후 비워준다.)
                                    group_box = []

                            elif cx.localName == "group":
                                # class 설정.
                                cx.setClass("items")

                                if cx.element.parentNode:
                                    # 부모/자식 관계 설정
                                    cx.element.parentNode.removeChild(cx.element)

                                # items group 목록에 추가.
                                group_items_list.append(cx.element)

                                # group 인 경우 자식에 존재하는 group 리스트에서 첫번째를 제외하고 hidden 처리한다.
                                childNodes_items = cx.element.childNodes
                                for ii, g_item in enumerate(childNodes_items):

                                    # 첫번째 제외. (items group 인 것만 대상으로 한다.)
                                    if ii > 0 and getEqElement(g_item).localName == "group":
                                        style_string = "display: none;"
                                        addElementStyle(getEqElement(g_item), style_string)

                    # items 리스트를 부모와 연결한다.
                    for g_item in group_items_list:
                        # new group 추가
                        c_group.element.appendChild(g_item)
