import os
import json
import time
import datetime
import inquirer
from dotenv import load_dotenv

from utils import HTTPRequest

load_dotenv(verbose=True)

if os.getenv('ID') is None or os.getenv('PASSWORD') is None:
    print("* 절대 아이디나 비밀번호 등 개인정보를 기록하지 않습니다. *")
    inputInfo = inquirer.prompt([
        inquirer.Text('id', message='아이디를 입력하세요. '),
        inquirer.Text('password', message='비밀번호를 입력하세요. '),
    ])
    with open('./.env', 'w', encoding='utf-8') as f:
        f.write(f'ID={inputInfo["id"]}\nPASSWORD={inputInfo["password"]}')
    os.system('cls' if os.name == 'nt' else 'clear')

try:
    with open("./config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    with open("./config.json", "w", encoding="utf-8") as f:
        f.write("{}")
        config = {}


def createToken() -> str:
    request: dict = HTTPRequest(
        url="https://ebsoc.co.kr/auth/api/v1/login",
        method="POST",
        json={"memberId": os.getenv("ID"), "memberPassword": os.getenv("PASSWORD")},
    )
    config["TOKEN"] = request["data"]["token"]
    config["DNS"] = request["data"]["memberInfo"]["memberSchoolInfo"]["hostName"]
    config["officeEdu"] = request["data"]["memberInfo"]["memberOfficeEdu"]
    config["schoolCode"] = request["data"]["memberInfo"]["memberSchoolInfo"][
        "schoolCode"
    ]
    for i in range(1, 6):
        if (
            request["data"]["memberInfo"]["memberSchoolInfo"].get(
                f"memberSchoolGrd{i}Yn"
            )
            == "Y"
        ):
            config[
                "schlGrdCd"
            ] = f'{request["data"]["memberInfo"]["memberSchoolInfo"]["schoolTypeCode"]}0{i}'
    config["userSequenceNo"] = request["data"]["memberInfo"]["memberSeq"]
    with open("./config.json", "w", encoding="utf-8") as w:
        json.dump(config, w, ensure_ascii=False, indent=4)
    return request["data"]["token"]


def lastCreateToken() -> None:
    if config.get("TOKEN") is None:
        createToken()
        return None
    check = HTTPRequest(
        url=f'https://{config["DNS"]}.ebsoc.co.kr/common/api/v1/school/info/{config["schoolCode"]}',
        method="GET",
        headers={"X-AUTH-TOKEN": config["TOKEN"]},
    )
    if check.get("status") == 403:
        createToken()
        return None


lastCreateToken()


with open("./config.json", "r", encoding="utf-8") as f:
    TOKEN = json.load(f)["TOKEN"]

menus = ["과목 조회 및 수업들 조회하기", "나가기"]


def getSubjects(pageNum: int):
    subjects = HTTPRequest(
        url=f'https://{config["DNS"]}.ebsoc.co.kr/cls/api/v1/school/schoolClassList/paged',
        method="POST",
        json={
            "offecCd": config["officeEdu"],
            "schoolCode": config["schoolCode"],
            "schoolAffairsYear": "2021",
            "schlGrdCd": config["schlGrdCd"],
            "classSeCd": "ALL",
            "searchWord": "",
            "orderType": "DESC",
            "userSequenceNo": config["userSequenceNo"],
            "pageNo": pageNum,
        },
        headers={"X-AUTH-TOKEN": TOKEN},
    )
    return subjects


while True:
    menu = inquirer.prompt(
        [
            inquirer.List(
                "menu",
                message="무슨 메뉴를 선택하시겠어요?",
                choices=menus,
            ),
        ]
    )
    if menu["menu"] == "나가기":
        exit()
    if menu["menu"] == menus[0]:
        presentPageNum = 1
        classInformations = {}
        firstRequest = getSubjects(presentPageNum)
        lastPage = firstRequest["data"]["lastPage"]
        classInformations[presentPageNum] = firstRequest["data"]["list"]
        while True:
            if classInformations.get(presentPageNum) is None:
                Page = getSubjects(presentPageNum)
                classInformations[presentPageNum] = Page["data"]["list"]
            classes = list(
                map(lambda z: z["className"], classInformations[presentPageNum])
            )
            classes.append("이전 페이지")
            classes.append("다음 페이지")
            classes.append(f"나가기")
            classes.append(f"종료")
            classes.append(f"[ {presentPageNum} / {lastPage} ]")
            classSelect = inquirer.prompt(
                [
                    inquirer.List(
                        "class",
                        message="어떤 과목을 선택하시겠습니까?",
                        choices=classes,
                    )
                ]
            )["class"]
            if classSelect == "이전 페이지":
                if presentPageNum == 1:
                    presentPageNum = lastPage
                else:
                    presentPageNum -= 1
                continue
            elif classSelect == "다음 페이지":
                if presentPageNum == lastPage:
                    presentPageNum = 1
                else:
                    presentPageNum += 1
                continue
            elif classSelect == "나가기":
                break
            elif classSelect == "종료":
                exit()
            elif classSelect == f"[ {presentPageNum} / {lastPage} ]":
                continue
