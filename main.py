import os
import json
import inquirer
from dotenv import load_dotenv

from utils import HTTPRequest

load_dotenv(verbose=True)

if os.getenv("ID") is None or os.getenv("PASSWORD") is None:
    print("* 절대 아이디나 비밀번호 등 개인정보를 기록하지 않습니다. *")
    userId = input("아이디를 입력하세요 : ")
    userPassword = input("비밀번호를 입력하세요 : ")
    with open("./.env", "w", encoding="utf-8") as f:
        f.write(f"ID={userId}\nPASSWORD={userPassword}")
    os.system("cls" if os.name == "nt" else "clear")

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
    for grade in range(1, 6):
        if (
            request["data"]["memberInfo"]["memberSchoolInfo"].get(
                f"memberSchoolGrd{grade}Yn"
            )
            == "Y"
        ):
            config[
                "schlGrdCd"
            ] = f'{request["data"]["memberInfo"]["memberSchoolInfo"]["schoolTypeCode"]}0{grade}'
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


def getClasses(pageNum: int):
    _classes = HTTPRequest(
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
    return _classes


def getSubjects(classId: str, pageNum: int):
    return HTTPRequest(
        f'https://{config["DNS"]}.ebsoc.co.kr/lecture/api/v1/{classId}/lesson/list/paged?openYn=Y&pageNo={pageNum}',
        method="GET",
        headers={"X-AUTH-TOKEN": TOKEN},
    )


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
        firstRequest = getClasses(presentPageNum)
        classInformations = {presentPageNum: firstRequest["data"]["list"]}
        lastPage = firstRequest["data"]["lastPage"]
        while True:
            if classInformations.get(presentPageNum) is None:
                Page = getClasses(presentPageNum)
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
                        message="어떤 교실을 선택하시겠습니까?",
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
            else:
                for i in classInformations[presentPageNum]:
                    if i["className"] == classSelect:
                        classUrlPath = i["classUrlPath"]
                        presentSubjectPage = 1
                        firstSubjectRequest = getSubjects(classUrlPath, presentSubjectPage)
                        try:
                            lastSubjectPage = firstSubjectRequest["data"]["lastPage"]
                        except KeyError:
                            print("수강 가능한 강좌가 없습니다.")
                            continue
                        try:
                            subjectInformations = {presentSubjectPage: firstSubjectRequest['data']['list']}
                            print(subjectInformations[presentSubjectPage])
                        except KeyError:
                            print("수강 가능한 강좌가 없습니다.")
                            continue
                        subjectSelectPages = subjectInformations[presentSubjectPage]
                        while True:
                            if subjectInformations.get(presentSubjectPage) is None:
                                Page = getSubjects(classUrlPath, presentSubjectPage)
                                subjectInformations[presentSubjectPage] = Page['data']['list']
                            subjectPages = list(map(lambda x: x["lessonName"], subjectInformations[presentSubjectPage]))
                            subjectPages.append("이전 페이지")
                            subjectPages.append("다음 페이지")
                            subjectPages.append("나가기")
                            subjectPages.append("종료")
                            selectSubject = inquirer.prompt([
                                inquirer.List("subject", message="어떤 과목을 선택하시겠습니까?", choices=subjectPages)
                            ])
                            if selectSubject["subject"] == "이전 페이지":
                                if presentSubjectPage == 1:
                                    presentSubjectPage = lastSubjectPage
                                else:
                                    presentSubjectPage -= 1
                            elif selectSubject["subject"] == "다음 페이지":
                                if presentSubjectPage == lastSubjectPage:
                                    presentSubjectPage = 1
                                else:
                                    presentSubjectPage += 1
                            elif selectSubject["subject"] == "나가기":
                                break
                            elif selectSubject["subject"] == "종료":
                                exit()
                            else:
                                for x in subjectInformations[presentSubjectPage]:
                                    if x["lessonName"] == selectSubject["subject"]:
                                        subjectUrlPath = x["lessonUrlPath"]
