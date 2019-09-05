# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
import logging

class model():
    def __init__(self):
        self.mail_host = "smtp.qq.com"  # 设置服务器
        self.mail_port = 25  # 默认端口
        self.mail_user = "1533165085@qq.com"    # 用户名
        self.mail_pass = "kfcqwrxtqktabafh"   # 密码

    def send(self, option):
        message = MIMEText(option['html'], 'html', 'utf-8')
        message['Subject'] = option['subject']
        message['From'] = self.mail_user
        message['To'] = ', '.join(option['to'])

        try:
            smtpObj = smtplib.SMTP(self.mail_host, self.mail_port)
            smtpObj.login(self.mail_user, self.mail_pass)
            smtpObj.sendmail(self.mail_user, option['to'], message.as_string())
            smtpObj.quit()
            logging.debug("邮件发送成功")
            return 1
        except Exception as e:
            logging.debug('邮件发送失败: ' + str(e))
            return 0


if __name__ == "__main__":
    myemail = model()
    # myemail.send({'to': ['1533165085@qq.com'], 'subject': '邮件发送测试', 'html': '<p>邮件内容...</p>'})
