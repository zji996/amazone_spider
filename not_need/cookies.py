import json

def parse_cookie_string(cookie_string):
    # 将输入的 Cookie 字符串拆分为键值对
    cookies = {}
    for item in cookie_string.split('; '):
        key, value = item.split('=', 1)
        cookies[key] = value
    return cookies

# 示例输入的 Cookie 字符串
cookie_string = ("regStatus=pre-register; AMCV_7742037254C95E840A4C98A6%40AdobeOrg=1585540135%7CMCIDTS%7C19941%7CMCMID%7C19724315496985863012806244868864463843%7CMCAAMLH-1723453443%7C9%7CMCAAMB-1723453443%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1722855844s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.0; "
                  "session-id=142-7280304-1156348; session-id-time=2082787201l; i18n-prefs=USD; ubid-main=132-0077205-3754266; lc-main=en_US; _mkto_trk=id:365-EFI-026&token:_mch-amazon.com-1722921643012-36954; "
                  "mbox=session#a0e6b4cdaea4429e88e20a1e6d4117fb#1722923504|PC#a0e6b4cdaea4429e88e20a1e6d4117fb.35_0#1786166444; AMCV_4A8581745834114C0A495E2B%40AdobeOrg=179643557%7CMCIDTS%7C19942%7CMCMID%7C14472145128540094343901263166432201734%7CMCAAMLH-1723526442%7C9%7CMCAAMB-1723526442%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1722928843s%7CNONE%7CMCAID%7CNONE%7CMCSYNCSOP%7C411-19949%7CvVersion%7C5.5.0; "
                  "s_nr=1722921653777-New; s_lv=1722921653778; skin=noskin; session-token=kkgQpgoNvQ/kOft4jkcWdgAchkx+j/GbSaPtlHeiNNw0jVMF9Fqvrm84/7nnUCG/ZKP+ek/gfxSvPGd2YEKs53nMlLfKxK/THMu5V9HhbZsgTLjLKl/7FW2klMU0eezdqhFkCAYQJcRqzlwkVWAmINuDTODj38SYxpaVVhZRzjGjODjn2uMUCMBMgu6TbpwgexSySK0xvZvL78HuRJTlMQNVSVA+E5o52ykWpWw/aidDRIHxmNlwCUU7tti1F/FPimwc9VdxIGIZ36sch5NNsWMsziIkkGajaifovjjkcqCqVbsi9Lpz0oF0k+YPbKsOp17CfYtx0tvSa5PUu1WvueVpJ2AXhbYL")

# 解析 Cookie 字符串
cookies = parse_cookie_string(cookie_string)

# 将 Cookie 字典转换为 JSON 格式
with open('cookies.json', 'w') as f:
    json.dump(cookies, f)
