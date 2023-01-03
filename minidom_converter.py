# -*- coding: utf-8 -*-

# Copyright (c) Inswave Systems. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

# USAGE
# python minidom_converter.py

# Environment
# python version : 3.7

from util import util
import traceback


class MinidomConverter:

    def __init__(self, log_flag):
        """Initialize this client for Compute Instance
        """

        # Log 파일 생성 여부.
        self.LOG_FLAG = log_flag

        pass

    """
        절대좌표 소스를 상대좌표 소스로 변경한다.
    """

    def exec_absolute_relative_convert_by_file(self, file_name):

        # log file name 구성.
        log_file_root, log_file_name, curr_yyyymmddhhmiss = util.get_log_file_name_with_file(file_name)

        # file_name 에서 result file_name 을 가져온다.
        source_xml_file_name, result_xml_file_name = util.get_source_and_result_file_name(file_name)

        try:

            # WebSquare file 변환 (절대좌표 ▶ 상대좌표)
            util.convert_wq_file(source_xml_file_name, result_xml_file_name)

            # Log
            file_nm = source_xml_file_name.split("/")[-1]
            log_message = "File '{}' has been converted successfully !!".format(file_nm)
            print("File [{}] has been converted successfully !!".format(file_nm))

            # Write log
            if self.LOG_FLAG == "Y":
                util.write_log_success(log_file_root, log_file_name, source_xml_file_name, result_xml_file_name, curr_yyyymmddhhmiss, log_message)

        except Exception as e:

            # Log
            file_nm = source_xml_file_name.split("/")[-1]
            log_message = "{}".format(traceback.format_exc())
            print("File [{}] has got an error !! [{}]".format(file_nm, log_message))

            # Write log
            if self.LOG_FLAG == "Y":
                util.write_log_error(log_file_root, log_file_name, source_xml_file_name, result_xml_file_name,
                                 curr_yyyymmddhhmiss, log_message)

    """
        절대좌표 소스를 상대좌표 소스로 변경한다.
    """

    def exec_absolute_relative_convert(self, dir_path):

        # log file name 구성.
        log_file_root, log_file_name, curr_yyyymmddhhmiss = util.get_log_file_name_with_folder(dir_path)

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
                log_message = "File '{}' has been converted successfully !!".format(file_nm)
                print("File [{}] has been converted successfully !!".format(file_nm))

                # Write log
                if self.LOG_FLAG == "Y":
                    util.write_log_success(log_file_root, log_file_name, source_xml_file_name, result_xml_file_name, curr_yyyymmddhhmiss, log_message)

            except Exception as e:

                # Log
                file_nm = source_xml_file_name.split("/")[-1]
                log_message = "{}".format(traceback.format_exc())
                print("File [{}] has got an error !! [{}]".format(file_nm, log_message))

                # Write log
                if self.LOG_FLAG == "Y":
                    util.write_log_error(log_file_root, log_file_name, source_xml_file_name, result_xml_file_name, curr_yyyymmddhhmiss, log_message)


# main process 실행
if __name__ == '__main__':

    ####################################################################################################
    # Params : python minidom_converter.py --dir-path "C:/PycharmProjects/test_ysjeong/Format_changer/xml_minidom/test/files"
    # Params : python minidom_converter.py --dir-path ./test/files --file-name ./test/files/065000100.xml --log-flag "Y"
    ####################################################################################################

    # Argument setting
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--dir-path', type=str, default="", dest='dir_path', help='work directory path')
    parser.add_argument('--file-name', type=str, default="", dest='file_name', help='file name')
    parser.add_argument('--log-flag', type=str, default="", dest='log_flag', help='log write flag')
    args = parser.parse_args()

    # Parameters setting
    dir_path = args.dir_path.strip()
    file_name = args.file_name.strip()
    log_flag = args.log_flag.strip()

    # log_flag 기본값 "Y"
    if len(log_flag.strip()) == 0:
        log_flag = "Y"

    # parameter 체크.
    if len(dir_path.strip()) + len(file_name.strip()) == 0:
        raise Exception("Please, enter dir-path or file-name")

    # minidom converter 생성
    minidom_converter = MinidomConverter(log_flag)

    # 1. file 단위 처리.
    # 2. folder 단위 recursive 처리.
    if len(file_name) > 0:
        minidom_converter.exec_absolute_relative_convert_by_file(file_name)
    else:
        minidom_converter.exec_absolute_relative_convert(dir_path)
