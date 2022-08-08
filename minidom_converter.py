# -*- coding: utf-8 -*-

# Copyright (c) Inswave Systems. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

# USAGE
# python minidom_converter.py

# Environment
# python version : 3.7

from util import util
import logging


class MinidomConverter:

    def __init__(self, b_debug_mode=False):
        """Initialize this client for Compute Instance
        """

        # DEBUG_MODE 가 True 인 경우만 실행.
        self.DEBUG_MODE = b_debug_mode

        # DEBUG_MODE parameter setting.
        if self.DEBUG_MODE:
            # logging setting
            util.set_logging_basic_config()

        pass

    """
        절대좌표 소스를 상대좌표 소스로 변경한다.
    """

    def exec_absolute_relative_convert_by_file(self, file_name):

        # file_name 에서 result file_name 을 가져온다.
        source_xml_file_name, result_xml_file_name = util.get_source_and_result_file_name(file_name)

        try:

            # WebSquare file 변환 (절대좌표 ▶ 상대좌표)
            util.convert_wq_file(source_xml_file_name, result_xml_file_name)

            # Log
            file_nm = source_xml_file_name.split("/")[-1]
            print("File [{}] has been converted successfully !!".format(file_nm))

            if self.DEBUG_MODE:
                logging.debug("File [{}] has been converted successfully !!".format(file_nm))

        except Exception as e:

            # Log
            file_nm = source_xml_file_name.split("/")[-1]
            print("File [{}] has got an error !! [{}]".format(file_nm, e))

            if self.DEBUG_MODE:
                logging.error("File [{}] has got an error !! [{}]".format(file_nm, e))

    """
        절대좌표 소스를 상대좌표 소스로 변경한다.
    """

    def exec_absolute_relative_convert(self, dir_path):

        # file 목록 조회
        source_xml_file_name_list, result_xml_file_name_list = util.get_files_by_dir(dir_path)

        # 2.relative, relative convert loop
        for i, source_file in enumerate(source_xml_file_name_list):

            try:
                # 파일명
                source_xml_file_name = source_file
                result_xml_file_name = result_xml_file_name_list[i]

                # WebSquare file 변환 (절대좌표 ▶ 상대좌표)
                util.convert_wq_file(source_xml_file_name, result_xml_file_name)

                # Log
                file_nm = source_xml_file_name.split("/")[-1]
                print("File [{}] has been converted successfully !!".format(file_nm))

                if self.DEBUG_MODE:
                    logging.debug("File [{}] has been converted successfully !!".format(file_nm))

            except Exception as e:

                # Log
                file_nm = source_xml_file_name.split("/")[-1]
                print("File [{}] has got an error !! [{}]".format(file_nm, e))

                if self.DEBUG_MODE:
                    logging.error("File [{}] has got an error !! [{}]".format(file_nm, e))


# main process 실행
if __name__ == '__main__':

    ####################################################################################################
    # Params : python minidom_converter.py --dir-path "C:/PycharmProjects/test_ysjeong/Format_changer/xml_minidom/test/files"
    # Params : python minidom_converter.py --dir-path ./test/files --file-name ./test/files/065000100.xml --debug-mode True
    ####################################################################################################

    # Argument setting
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--dir-path', type=str, default="", dest='dir_path', help='work directory path')
    parser.add_argument('--file-name', type=str, default="", dest='file_name', help='file name')
    parser.add_argument('--debug-mode', type=bool, default=False, dest='debug_mode', help='debug mode')
    args = parser.parse_args()

    # Parameters setting
    dir_path = args.dir_path.strip()
    file_name = args.file_name.strip()
    b_debug_mode = args.debug_mode

    # TODO : 삭제
    # file_name = "C:/PycharmProjects/test_ysjeong/Format_changer/xml_minidom/test/files/065000100.xml"

    # Default parameters setting
    # b_debug_mode = False
    # print("b_debug_mode:{}".format(b_debug_mode))

    # minidom converter 생성
    minidom_converter = MinidomConverter(b_debug_mode)

    # TODO : 삭제
    if len(dir_path.strip()) == 0:
        # dir_path = "C:/PycharmProjects/test_ysjeong/Format_changer/xml_minidom/test/files"
        dir_path = "./test/files"

    # 1. file 단위 처리.
    # 2. folder 단위 recursive 처리.
    if len(file_name) > 0:
        minidom_converter.exec_absolute_relative_convert_by_file(file_name)
    else:
        minidom_converter.exec_absolute_relative_convert(dir_path)
