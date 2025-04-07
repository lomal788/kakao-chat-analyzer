import re
import os
from datetime import datetime
from tqdm import tqdm

# https://github.com/uoneway/kakaotalk_msg_preprocessor

# kakaotalk 메시지 중 날짜표현 패턴
# 이를 사용하여 파일이 추출된 소스와 메시지 구분
kakaotalk_datetime_pattern_dict = {'window_ko_date': r"-{15} [0-9]{4}년 [0-9]{1,2}월 [0-9]{1,2}일 \S요일 -{15}",
                                'window_ko_time': r"((\[)([^\[])+(\])) ((\[오)\S [0-9]{1,2}:[0-9]{1,2}(\]))",
                                'window_ko': r"저장한 날짜 : ([0-9]){4}-([0-9]){1,2}-([0-9]){1,2} ([0-9]){1,2}:([0-9]){1,2}:([0-9]){1,2}",

                                'iphone_ko': r"저장한 날짜 : ([0-9]){4}. ([0-9]){1,2}. ([0-9]){1,2}. 오\S ([0-9]){1,2}:([0-9]){1,2}",
                                'iphone_ko_date': r"([0-9]){4}. ([0-9]){1,2}. ([0-9]){1,2}. (오\S) ([0-9]){1,2}:([0-9]){1,2}",
                                'iphone_ko_time': r"([0-9]){1,2}:([0-9]){1,2}",

                                'android_ko': r"([0-9]){4}년 ([0-9]){1,2}월 ([0-9]){1,2}일 오\S ([0-9]){1,2}:([0-9]){1,2}",
                                'android_en': r"([A-z])+ ([0-9]){1,2}, ([0-9]){4}, ([0-9]){1,2}:([0-9]){1,2} \SM",
                                'android_en': r"([A-z])+ ([0-9]){1,2}, ([0-9]){4} ([A-z])+ ([0-9]){1,2}:([0-9]){1,2}",
                                'android_en_date': r"([A-z])+ ([0-9]){1,2}, ([0-9]){4} ([A-z])+ ([0-9]){1,2}:([0-9]){1,2}",
                                'android_en_time': r"[0-9]{1,2}:[0-9]{1,2}\s?(?:AM|PM|am|pm)",
                                    }

kakaotalk_export_file_dict = {
    'iphone_ko' : r'Talk_([0-9]{4}).([0-9]{1,2}).([0-9]{1,2}) ([0-9]{1,2})_([0-9]{1,2})-([0-9]{1,100})'
}

def check_export_file_type(file_path,
                            datetime_pattern_dict=kakaotalk_datetime_pattern_dict):
    """
    Check the device type and language of kakaotalk_export_file.
    It is done based on datetime patterns in file
    
    Parameters
    ----------
    file_path: string

    datetime_pattern_dict: dict
        datetime_pattern used i kaotalk_export_file

    Returns
    -------
    file_type: string
        one of among 'window_ko', 'android_ko' or 'android_en'
    """

    # 파일의 두 번째 줄(저장한 날짜 : /Date Saved : ) 부분의 날짜형식으로 구분
    kakaotalk_include_date_pattern_dict = {'pc_ko': r"([0-9]){4}-([0-9]){1,2}-([0-9]){1,2} ([0-9]){1,2}:([0-9]){1,2}",
                                'mobile_ko': r"([0-9]){4}년 ([0-9]){1,2}월 ([0-9]){1,2}일 오\S ([0-9]){1,2}:([0-9]){1,2}",
                                'mobile_en': r"([A-z])+ ([0-9]){1,2}, ([0-9]){4}, ([0-9]){1,2}:([0-9]){1,2} \SM",}
    
    with open(file_path, 'r', encoding='UTF8') as f:
        for counter in range(5):
            line = f.readline()
            if not line: break

            for file_type, pattern in datetime_pattern_dict.items():
                if re.search(pattern, line):
                    # print(pattern, line)
                    
                    return '_'.join(file_type.split('_')[:2])
    
    print("Error: Cannot know the device type and language of the file.\n",
          f"Please check the file is a kakaotalk export file or the export enviroment is in among {str(list(kakaotalk_include_date_pattern_dict.keys()))}")

def _str_to_datetime(file_type, text):
    kakaotalk_strptime_pattern_dict = {'ko': '%Y년 %m월 %d일 %p %I:%M',
                                       'iphone_ko': '%Y %m, %d, %p:%I %M',
                                        'en': '%B %d, %Y, %I:%M %p',
                                        }

    language = file_type.split('_')[1]

    if language == 'ko':
        text = text.replace('오전', 'AM')
        text = text.replace('오후', 'PM')

    if file_type == 'iphone_ko':
        language='iphone_ko'

    text_dt = datetime.strptime(text, kakaotalk_strptime_pattern_dict[language])
    return text_dt

def file_search(dirname):
    filenames = os.listdir(dirname)
    iphone_list = {}
    file_list = []

    for filename in filenames:
        full_filename = os.path.join(dirname, filename)
        ext = os.path.splitext(full_filename)[-1]

        if ext.lower() == '.txt':
            if re.search(kakaotalk_export_file_dict['iphone_ko'], full_filename):
                data = re.findall(kakaotalk_export_file_dict['iphone_ko'],full_filename)
                data = data[0]
                file_type = f"Talk_{data[0]}.{data[1]}.{data[2]} {data[3]}_{data[4]}-"

                if f"{dirname}{file_type}merged.txt" != full_filename:
                    if file_type in iphone_list:
                        iphone_list[file_type].append(full_filename)
                    else:
                        iphone_list[file_type] = [full_filename]
            else:
                file_list.append(full_filename)

    if len(iphone_list) > 0:
        print('분산된 파일 합치기를 시작합니다.')
    for item in iphone_list:
        if os.path.isfile(f"{dirname}{item}merged.txt") is False:
            merge_iphone_file(dirname, item, iphone_list[item])
            file_list.append(f"{dirname}{item}merged.txt")

    return file_list

def merge_iphone_file(dirname, output_file_name, file_names):
    with open(f'{dirname}{output_file_name}merged.txt', 'w', encoding='utf-8') as outfile:
        for idx,filename in enumerate(file_names):
            with open(filename, mode="r", encoding='utf-8') as file:
                for line_index,line in enumerate(file):
                    if idx > 0:
                        if line_index > 4:
                            outfile.write(line)
                    else:
                        outfile.write(line)
            file.close()
    outfile.close()

def parse(file_type, file_path,
                datetime_pattern_dict=kakaotalk_datetime_pattern_dict):
    """
    Parsing the text from a kaotalk_export_file.
    This parser divide messages based on datetime_pattern.
    
    Parameters
    ----------
    file_type: string
        one of among 'window_ko', 'android_ko' or 'android_en'

    file_path: string

    datetime_pattern_dict: dict
        datetime_pattern used i kaotalk_export_file

    Returns
    -------
    msgs: list
        The messages are list of dictionary.
        Each dictionary compose of the informtion of each message.
        And it has keys, 'datetime,'user_name' and 'text'.
    """

    msgs = []
    estimated_lines = 0

    with open(file_path, 'r', encoding='UTF8') as f:
        for _ in f:
            estimated_lines += 1
    f.close()

    if file_type == 'window_ko':     # window
        date_pattern = datetime_pattern_dict['window_ko_date']
        time_pattern = datetime_pattern_dict['window_ko_time']
        my_datetime = ""

        with open(file_path, encoding='UTF8') as file: 
            # 줄바꿈되어있는 경우도 묶어주기 위해 buffer 사용
            buffer = ''
            date = ''

            for line in file:
                # window파일의 데이트str(--------------- 2020년 6월 28일 일요일 ---------------)이거나 시간 str([김한길] [오후 2:15] htt)이면

                if line.find("님이 들어왔습니다.") > -1:
                    user_name = line.replace('님이 들어왔습니다.', '')
                    msgs.append({'datetime': my_datetime,
                                        'user_name': user_name.replace('\n',''),
                                        'type': 'enter'
                        })
                    continue
                elif line.find("님이 나갔습니다.") > -1:
                    user_name = line.replace('님이 나갔습니다.', '')
                    msgs.append({'datetime': my_datetime,
                                        'user_name': user_name.replace('\n',''),
                                        'type': 'leave'
                    })
                    continue
                elif line.find("님을 내보냈습니다.") > -1 and not re.match(date_pattern, line) and not re.match(time_pattern, line):
                    user_name = line.replace('님을 내보냈습니다.', '')
                    msgs.append({'datetime': my_datetime,
                                        'user_name': user_name.replace('\n',''),
                                        'type': 'kicked'
                    })
                    continue
                elif line.find('채팅방 관리자가 메시지를 가렸습니다') > -1:
                    # msgs.append({'datetime': my_datetime,
                    #              'type': 'delText'
                    # })
                    continue
                elif line.find('님이 부방장이 되었습니다') > -1:
                    # msgs.append({'datetime': my_datetime,
                    #              'type': 'becomeManager'
                    # })
                    continue
                elif line.find('님이 부방장에서 해제되었습니다') > -1:
                    # msgs.append({'datetime': my_datetime,
                    #              'type': 'delManager'
                    # })
                    continue
                elif line.find('샵검색') > -1:
                    # msgs.append({'datetime': my_datetime,
                    #              'type': 'delManager'
                    # })
                    continue
                elif line.find('선물 게임이 종료되었습니다') > -1 or line.find('선물게임이 종료되었습니다')  > -1:
                    # msgs.append({'datetime': my_datetime,
                    #              'type': 'delManager'
                    # })
                    continue
                
                if re.match(date_pattern, line) or re.match(time_pattern, line):
                    # buffer가 time_pattern으로 시작하는 경우만 추가해주기
                    if re.match(time_pattern, buffer):  
                        buffer_tokens = buffer.split(']', maxsplit=2)
                        user_name = buffer_tokens[0].replace('[', '').strip()
                        time = buffer_tokens[1].replace('[', '').strip()
                        my_datetime = _str_to_datetime(file_type, f"{date} {time}")
                        text = buffer_tokens[2].strip()

                        if text == "운세":
                            msgs.append({'datetime': my_datetime,
                                         'user_name': user_name,
                                        'type': 'lucky'
                            })
                        
                        msgs.append({'datetime': my_datetime,
                                        'user_name': user_name,
                                        'text': text,
                                        'type':'msg'
                        })

                    if re.match(date_pattern, line):  # window파일의 데이트str이면
                        date = line.replace('-', '').strip().rsplit(" ", 1)[0]
                        buffer = ''
                    else:  #  window파일의 시간 str이면
                        buffer = line

                else:
                    buffer += line
    elif file_type == 'android_en':
        datetime_pattern = datetime_pattern_dict[file_type]
        msg_exist_check_pattern = datetime_pattern + ",.*:"
        date_pattern = datetime_pattern_dict['android_en_date']
        time_pattern = datetime_pattern_dict['android_en_time']
        my_datetime = ""
        count = 0

        with open(file_path, mode="r", encoding='utf-8') as file: 
            text = ''
            with tqdm(total=estimated_lines, unit="line", desc="Reading file") as pbar:
                for line in file:
                    count+=1
                    pbar.update(1)
                    data = None
                    try:
                        if line.strip() == '':
                            continue
                        data = re.match(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)",line)
                    
                        if data and re.search(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)?, ([^:]*)? : (.*)",line):
                            data = re.findall(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)?, ([^:]*)? : (.*)",line)
                            data = data[0]
                            my_datetime = _str_to_datetime(file_type, f"{data[0]} {data[1]}, {data[2]}, {data[3]}:{data[4]} {data[5]}")
                            user_name = data[6].strip()

                            if text != '':
                                msgs.append({'datetime': my_datetime,
                                            'user_name': user_name,
                                            'text': text,
                                            'urls': url_msg_extract(text),
                                            'type': 'msg'
                                })

                            text = data[7].strip()

                            continue
                        elif re.match(datetime_pattern, line) is None and line.strip() != '':
                            text+= '\n'+line
                            continue
                        elif line.strip() != '':
                            text = ''
                            if line.find('This message has been hidden by the chatroom managers.') > -1:
                                # msgs.append({'datetime': my_datetime,
                                #             'type': 'delText'
                                # })
                                continue
                            elif line.find('joined this chatroom.') > -1:
                                line = line.replace('joined this chatroom.', '')
                                temp_data = re.findall(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)?, (.*)",line)
                                temp_data = temp_data[0]
                                my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                temp_user_name = temp_data[6].strip()

                                msgs.append({'datetime': my_datetime,
                                            'user_name': temp_user_name,
                                            'type': 'enter'
                                })

                                continue
                            elif line.find('left this chatroom.') > -1:
                                line = line.replace('left this chatroom.', '')
                                temp_data = re.findall(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)?, (.*)",line)
                                temp_data = temp_data[0]
                                my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                temp_user_name = temp_data[6].strip()
                                
                                msgs.append({'datetime': my_datetime,
                                            'user_name': temp_user_name,
                                            'type': 'leave'
                                })
                                continue
                            elif line.find('has been removed from this chatroom.') > -1:
                                line = line.replace('has been removed from this chatroom.', '')
                                temp_data = re.findall(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)?, (.*)",line)
                                temp_data = temp_data[0]
                                my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                temp_user_name = temp_data[6].strip()
                                
                                msgs.append({'datetime': my_datetime,
                                            'user_name': temp_user_name,
                                            'type': 'kicked'
                                })
                                continue
                            elif line.find('is no longer an admin.') > -1:
                                line = line.replace('is no longer an admin.', '')
                                temp_data = re.findall(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)?, (.*)",line)
                                temp_data = temp_data[0]
                                my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                temp_user_name = temp_data[6].strip()
                                
                                msgs.append({'datetime': my_datetime,
                                            'user_name': temp_user_name,
                                            'type': 'no_admin'
                                })
                                continue
                            elif line.find('has been assigned as the admin.') > -1:
                                line = line.replace('has been assigned as the admin.', '')
                                temp_data = re.findall(r"([A-z]{1,12})+ ([0-9]{1,2}), ([0-9]{4}) [A-z]+ ([0-9]{1,2}):([0-9]{1,2})\s?(AM|PM|am|pm)?, (.*)",line)
                                temp_data = temp_data[0]
                                my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                temp_user_name = temp_data[6].strip()
                                
                                msgs.append({'datetime': my_datetime,
                                            'user_name': temp_user_name,
                                            'type': 'admin'
                                })
                                continue
                            elif re.search(r"[A-z]{1,12}+ [0-9]{1,2}, [0-9]{4} [A-z]+ [0-9]{1,2}:[0-9]{1,2}\s?(?:AM|PM|am|pm), (?:Moderator has hidden ([0-9]{1,10}) message\(s\).)",line):
                                delete_msg_count = re.findall(r"[A-z]{1,12}+ [0-9]{1,2}, [0-9]{4} [A-z]+ [0-9]{1,2}:[0-9]{1,2}\s?(?:AM|PM|am|pm), (?:Moderator has hidden ([0-9]{1,10}) message\(s\).)",line)[0]

                                msgs.append({'datetime': my_datetime,
                                            'count': delete_msg_count,
                                            'type': 'hidden_messages'
                                })
                                # print('관리자 삭제',delete_msg_count,line)
                                continue
                            else:
                                text = ''
                                continue
                    except Exception as e:
                        print('오류발생 : ',e, line)
                        continue


                    # 선착순 선물 게임을 시작합니다! 기회는 단 [0-9]{1,10}분간, 선착순 ([0-9]{1,10})명에게!
            file.close()

    elif file_type == 'iphone_ko':
        datetime_pattern = datetime_pattern_dict[file_type]
        msg_exist_check_pattern = datetime_pattern + ",.*:"
        date_pattern = datetime_pattern_dict['iphone_ko_date']
        time_pattern = datetime_pattern_dict['iphone_ko_time']
        my_datetime = ""
        count = 0

        with open(file_path, mode="r", encoding='utf-8') as file: 
            text = ''
            with tqdm(total=estimated_lines, unit="line", desc="Reading file") as pbar:
                for line in file:
                    count+=1
                    pbar.update(1)
                    data = None
                    try:
                        if line.strip() == '':
                            continue
                        
                        data = re.match(r"([0-9]){4}. ([0-9]){1,2}. ([0-9]){1,2}. (오\S) ([0-9]){1,2}:([0-9]){1,2}",line)

                        if data and re.search(r"([0-9]){4}. ([0-9]){1,2}. ([0-9]){1,2}. (오\S) ([0-9]){1,2}:([0-9]){1,2}, ([^:]*)? : (.*)",line):
                            data = re.findall(r"([0-9]{4}). ([0-9]{1,2}). ([0-9]{1,2}). (오\S) ([0-9]{1,2}):([0-9]{1,2}), ([^:]*)? : (.*)",line)
                            data = data[0]
                            my_datetime = _str_to_datetime(file_type, f"{data[0]} {data[1]}, {data[2]}, {data[3]}:{data[4]} {data[5]}")
                            user_name = data[6].strip()

                            if text != '':
                                msgs.append({'datetime': my_datetime,
                                            'user_name': user_name,
                                            'text': text.replace('\u200b',''),
                                            'urls': url_msg_extract(text),
                                            'type': 'msg'
                                })

                            text = data[7].strip()

                            continue
                        elif re.match(datetime_pattern, line) is None and line.strip() != '':

                            if re.search(r"([0-9]){4}. ([0-9]){1,2}. ([0-9]){1,2}. (오\S) ([0-9]){1,2}:([0-9]){1,2}: (.*)",line) :
                                if text != '':
                                    msgs.append({'datetime': my_datetime,
                                                'user_name': user_name,
                                                'text': text.replace('\u200b',''),
                                                'urls': url_msg_extract(text),
                                                'type': 'msg'
                                    })
                                    text = ''
                                if line.find('님이 들어왔습니다.') > -1:
                                    line = line.replace('님이 들어왔습니다.', '')
                                    temp_data = re.findall(r"([0-9]{4}). ([0-9]{1,2}). ([0-9]{1,2}). (오\S) ([0-9]{1,2}):([0-9]{1,2}): (.*)",line)
                                    temp_data = temp_data[0]
                                    my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                    temp_user_name = temp_data[6].strip()

                                    msgs.append({'datetime': my_datetime,
                                                'user_name': temp_user_name,
                                                'type': 'enter'
                                    })

                                    continue
                                elif line.find('님이 나갔습니다.') > -1:
                                    line = line.replace('님이 나갔습니다.', '')
                                    temp_data = re.findall(r"([0-9]{4}). ([0-9]{1,2}). ([0-9]{1,2}). (오\S) ([0-9]{1,2}):([0-9]{1,2}): (.*)",line)
                                    temp_data = temp_data[0]
                                    my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                    temp_user_name = temp_data[6].strip()
                                    
                                    msgs.append({'datetime': my_datetime,
                                                'user_name': temp_user_name,
                                                'type': 'leave'
                                    })
                                    continue
                                elif line.find('님을 내보냈습니다.') > -1:
                                    line = line.replace('님을 내보냈습니다.', '')
                                    temp_data = re.findall(r"([0-9]{4}). ([0-9]{1,2}). ([0-9]{1,2}). (오\S) ([0-9]{1,2}):([0-9]{1,2}): (.*)",line)
                                    temp_data = temp_data[0]
                                    my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                    temp_user_name = temp_data[6].strip()
                                    
                                    msgs.append({'datetime': my_datetime,
                                                'user_name': temp_user_name,
                                                'type': 'kicked'
                                    })
                                    continue
                                elif line.find('님이 부방장에서 해제되었습니다.') > -1:
                                    line = line.replace('님이 부방장에서 해제되었습니다.', '')
                                    temp_data = re.findall(r"([0-9]{4}). ([0-9]{1,2}). ([0-9]{1,2}). (오\S) ([0-9]{1,2}):([0-9]{1,2}): (.*)",line)
                                    temp_data = temp_data[0]
                                    my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                    temp_user_name = temp_data[6].strip()
                                    
                                    msgs.append({'datetime': my_datetime,
                                                'user_name': temp_user_name,
                                                'type': 'no_admin'
                                    })
                                    continue
                                elif line.find('님이 부방장이 되었습니다.') > -1:
                                    line = line.replace('님이 부방장이 되었습니다.', '')
                                    temp_data = re.findall(r"([0-9]{4}). ([0-9]{1,2}). ([0-9]{1,2}). (오\S) ([0-9]{1,2}):([0-9]{1,2}): (.*)",line)
                                    temp_data = temp_data[0]
                                    my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                    temp_user_name = temp_data[6].strip()
                                    
                                    msgs.append({'datetime': my_datetime,
                                                'user_name': temp_user_name,
                                                'type': 'admin'
                                    })
                                    continue
                                elif line.find('채팅방 관리자가 메시지를 가렸습니다.') > -1:
                                    line = line.replace('채팅방 관리자가 메시지를 가렸습니다.', '')
                                    temp_data = re.findall(r"([0-9]{4}). ([0-9]{1,2}). ([0-9]{1,2}). (오\S) ([0-9]{1,2}):([0-9]{1,2}): (.*)",line)
                                    temp_data = temp_data[0]
                                    my_datetime = _str_to_datetime(file_type, f"{temp_data[0]} {temp_data[1]}, {temp_data[2]}, {temp_data[3]}:{temp_data[4]} {temp_data[5]}")
                                    
                                    msgs.append({'datetime': my_datetime,
                                                'count': 1,
                                                'type': 'hidden_messages'
                                    })
                                    continue

                            text+= '\n'+line
                            continue
                        elif line.strip() != '':
                            text = ''
                            continue
                    except Exception as e:
                        print('오류발생 : ',e, line)
                        continue


                    # 선착순 선물 게임을 시작합니다! 기회는 단 [0-9]{1,10}분간, 선착순 ([0-9]{1,10})명에게!
            file.close()

    else: # android
        datetime_pattern = datetime_pattern_dict[file_type]
        msg_exist_check_pattern = datetime_pattern + ",.*:"
        
        with open(file_path, encoding='UTF8') as file: 
            # 줄바꿈되어있는 경우도 저장하기 위해 buffer 사용
            buffer=''
            for line in file:
                if re.match(datetime_pattern, line):
                    if re.match(msg_exist_check_pattern, buffer):
                        
                        temp_01_2_tokens = buffer.split(" : ", maxsplit=1)
                        temp_0_1_tokens = temp_01_2_tokens[0].rsplit(",", maxsplit=1)

                        my_datetime = temp_0_1_tokens[0].strip()
                        my_datetime = _str_to_datetime(file_type, my_datetime)
                        user_name = temp_0_1_tokens[1].strip()
                        text = temp_01_2_tokens[1].strip()
                        msgs.append({'datetime': my_datetime,
                                    'user_name': user_name,
                                    'text': text,
                                    'type':'msg'
                        })

                    buffer = line
                else:
                    buffer += line
    
    return msgs


def _url_extract(text):
    regex = r'(https?://[^\s]+)'
    urls = []
    if re.match(regex, text):
        urls = re.findall(regex, text)

    return urls

def url_msg_extract(text):
    url_msgs = []

    urls = _url_extract(text)

    if urls:
        for url in urls:
            url_msgs.append(''.join(url))

    return url_msgs