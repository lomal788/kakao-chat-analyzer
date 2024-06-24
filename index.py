import sys
import os
import pandas as pd
from wordcloud import WordCloud
from PIL import Image
# from konlpy.tag import Okt
from datetime import datetime

# konlpy 형태소 분석

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')
sys.path.insert(0, PARENT_DIR)

import kakaotalk_msg_preprocessor

blockMsg = ['사진\n', 'ㅜ', 'ㅠ', 'ㅋ', 'ㅎ', 'ㅗ', '샵검색', 'ㄷ', 'ㅡ', 'ㄹㅇ', '근데', '진짜', 'ㅇ', '해외 종목 정보', '종목정보', '삭제된 메시지입니다.']


# TEST_DIR + "/datasets/kakao.txt"
file_path_list =["./datasets/kakao.txt",
                ]

if __name__ == '__main__':
    for file_path in file_path_list:
        text = ""
        print(f"------------{file_path} test start-------------------")
        file_type = kakaotalk_msg_preprocessor.check_export_file_type(file_path)
        print(file_type)

        stopwords = pd.read_csv("https://raw.githubusercontent.com/yoonkt200/FastCampusDataset/master/korean_stopwords.txt").values.tolist()
        
        messages = kakaotalk_msg_preprocessor.parse(file_type, file_path)

        print("파싱완료 대화 분석시작")

        user = {}
        gift_send_user_list = {}
        gift_receive_user_list = {}
        user_kicked_list = {}
        total_chat_cnt = 0
        user_aa = []
        
        for item in messages:

            # userName = item["user_name"].replace('\n','')

            if item["user_name"] is not None and user.get(item["user_name"]) is None:
                user[item["user_name"]] = {
                    'chat_percent':'',
                    'chat_cnt':0,
                    'leave_cnt':0,
                    'enter_cnt':0,
                    'kick_cnt':0,
                    'gift_send_cnt':0,
                    'gift_receive_cnt':0,
                    'last_gift_send_date':None,
                    'last_gift_receive_date':None,
                    'last_chat_date':None,
                    'last_kick_date':None,
                    'last_leave_date':None,
                    'last_enter_date':None
                    # 'customOX':'X'
                }


            if item["type"] == "msg" and (item["text"].find("선물 게임을 시작합니다") > -1 or item["text"].find("선물게임을 시작합니다") > -1 ):
                if gift_send_user_list.get(item["user_name"]) is None:
                    gift_send_user_list[item["user_name"]] = 0
                gift_send_user_list[item["user_name"]] = gift_send_user_list[item["user_name"]] + 1
                user[item["user_name"]]["gift_send_cnt"] = gift_send_user_list[item["user_name"]]
                user[item["user_name"]]["last_gift_send_date"] = item["datetime"]
                continue

            if item["type"] == "msg" and item["text"].find("선물에 당첨되었어요") > -1:
                if gift_receive_user_list.get(item["user_name"]) is None:
                    gift_receive_user_list[item["user_name"]] = 0
                gift_receive_user_list[item["user_name"]] = gift_receive_user_list[item["user_name"]] + 1
                user[item["user_name"]]["gift_receive_cnt"] = gift_receive_user_list[item["user_name"]]
                user[item["user_name"]]["last_gift_receive_date"] = item["datetime"]
                continue

            if item["type"] == 'kicked':
                user_kicked_list[item["user_name"]] = 0
                user[item["user_name"]]["kick_cnt"] = user[item["user_name"]]["kick_cnt"] + 1
                user[item["user_name"]]["last_kick_date"] = item["datetime"]

            if item["type"] == 'leave':
                user[item["user_name"]]["leave_cnt"] = user[item["user_name"]]["leave_cnt"] + 1
                user[item["user_name"]]["last_leave_date"] = item["datetime"]
            if item["type"] == 'enter':
                user[item["user_name"]]["enter_cnt"] = user[item["user_name"]]["enter_cnt"] + 1
                user[item["user_name"]]["last_enter_date"] = item["datetime"]
                

            if item["type"] != 'msg':
                continue
            elif item["user_name"] != "팬다 Jr." and item["user_name"].find("드리고") == -1  and item["user_name"].find("𝗗𝗥𝗘𝗔𝗚𝗢") == -1:

                    
                msg = item["text"]
                tempText = msg
                # okt = Okt()  # 형태소 추출
                # nouns = okt.nouns(tempText)
                # tempText = [x for x in tempText if x not in stopwords]
                # print(tempText)
                # tempText = " ".join(nouns)
                for bm in blockMsg :
                    tempText = tempText.replace(bm, '')

                if tempText.find('http') > -1 or tempText.find('https') > -1 or tempText.find('이모티콘') > -1 or tempText.find('@') > -1:
                    continue
                # print(nouns)
                text += tempText
                # if item["user_name"] == '닉네임':
                #     user_aa.append(item["datetime"].strftime('%Y-%m-%d %H:%M'))
                #     text += tempText

            total_chat_cnt = total_chat_cnt + 1
            user[item["user_name"]]["chat_cnt"] = user[item["user_name"]]["chat_cnt"] + 1
            user[item["user_name"]]["last_chat_date"] = item["datetime"]


            # msgs.append({'datetime': my_datetime,
            #                             'user_name': user_name,
            #                             'type': 'kicked'
            #         })

        # print(user)
        # 총 받은선물 갯수 리스트
        # user = sorted(user.items(),key=lambda item : item[1],reverse=True)
        # aa = 0
        # for item in user:
        #     print(item[0],item[1],"회")
        #     aa = aa+item[1]
        # print(aa)

        # user_kicked_list[item["user_name"]]
        # print(user_kicked_list)
        # for item in user_kicked_list:
        #     print(item.replace('\n', ''))

        # gift_send_user_list = sorted(gift_send_user_list.items(),key=lambda item : item[1],reverse=True)
        # aa = 0
        # for item in gift_send_user_list:
        #     print(item[0],item[1],"회")
        #     aa = aa+item[1]
        # print(aa)
        # print(user)
        for item in user:

            if int(user[item]["chat_cnt"]) > 0:
                user[item]["chat_percent"] = round((user[item]["chat_cnt"] / total_chat_cnt ) * 100, 4)


            if user[item]["last_gift_send_date"] is not None:
                user[item]["last_gift_send_date"] = user[item]["last_gift_send_date"].strftime('%Y-%m-%d %H:%M')
            if user[item]["last_gift_receive_date"] is not None:
                user[item]["last_gift_receive_date"] = user[item]["last_gift_receive_date"].strftime('%Y-%m-%d %H:%M')
            if user[item]["last_chat_date"] is not None:
                user[item]["last_chat_date"] = user[item]["last_chat_date"].strftime('%Y-%m-%d %H:%M')
            if user[item]["last_kick_date"] is not None:
                user[item]["last_kick_date"] = user[item]["last_kick_date"].strftime('%Y-%m-%d %H:%M')
            if user[item]["last_leave_date"] is not None:
                user[item]["last_leave_date"] = user[item]["last_leave_date"].strftime('%Y-%m-%d %H:%M')
            if user[item]["last_enter_date"] is not None:
                user[item]["last_enter_date"] = user[item]["last_enter_date"].strftime('%Y-%m-%d %H:%M')

        # print(total_chat_cnt)
        file_path = "readMe.txt"
        with open(file_path, "w", encoding='UTF8') as file:
            file.write("총 채팅 갯수 : "+str(total_chat_cnt)+"\n")
        
        # file_path = "user_aa.txt"
        # with open(file_path, "w", encoding='UTF8') as file:
        #     file.write(str(user_aa))

        

        # file_path = "userList.txt"
        # with open(file_path, "w", encoding='UTF8') as file:
        #     file.write(str(user) + "\n")

        file_path = "userInfo.csv"
        with open(file_path, "w", encoding='UTF8') as file:
            file.write("이름,채팅 점유율, 채팅횟수,퇴장횟수,입장횟수,강퇴횟수,선물받은횟수,선물횟수,최근 선물받은 날짜, 최근 선물한 날짜, 최근 강퇴날짜,최근 퇴장날짜,최근 입장 날짜, 최근 채팅날짜\n")
            for item in user:
                userName = item
                chat_percent = user[item]["chat_percent"]
                chat_cnt = user[item]["chat_cnt"]
                leave_cnt = user[item]["leave_cnt"]
                enter_cnt = user[item]["enter_cnt"]
                kick_cnt = user[item]["kick_cnt"]
                gift_send_cnt = user[item]["gift_send_cnt"]
                gift_receive_cnt = user[item]["gift_receive_cnt"]
                last_gift_send_date = user[item]["last_gift_send_date"]
                last_gift_receive_date = user[item]["last_gift_receive_date"]
                last_chat_date = user[item]["last_chat_date"]
                last_kick_date = user[item]["last_kick_date"]
                last_leave_date = user[item]["last_leave_date"]
                last_enter_date = user[item]["last_enter_date"]
                # customOX = user[item]["customOX"]

                file.write(f"{userName},{chat_percent},{chat_cnt},{leave_cnt},{enter_cnt},{kick_cnt},{gift_receive_cnt},{gift_send_cnt},{last_gift_receive_date},{last_gift_send_date},{last_kick_date},{last_leave_date},{last_enter_date},{last_chat_date}\n")


        print("채팅 파싱완료")
        font = 'NanumBarunGothicBold.ttf'

        wc = WordCloud(font_path=font, background_color="white", width=1920, height=1080)
        # wc = WordCloud(background_color="white", width=600, height=400)
        wc.generate(text)
        wc.to_file("result.png")
        print("작업완료")

        # url_messages = kakaotalk_msg_preprocessor.url_msg_extract(file_type, messages)
        # print(url_messages)

        # input_df = pd.DataFrame.from_dict(url_messages)[['datetime', 'url']]
        # input_df.rename(columns = {'datetime' : 'clip_at'}, inplace = True)
        # print(input_df)
