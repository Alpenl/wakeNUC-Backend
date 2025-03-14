# 获取RSA公钥的URL，用于加密密码
public_key_url = "https://zhrz.nuc.edu.cn/cas/v2/getPubKey"
# 统一身份认证系统登录页面URL，service参数指定登录成功后的跳转地址
index_url = "https://zhrz.nuc.edu.cn/cas/login?service=https%3A%2F%2Fzhmh.nuc.edu.cn%2F"
# 登录测试URL，用于验证登录状态是否有效
login_test_url = "https://zhmh.nuc.edu.cn/personal-center"
# 教务系统首页URL，用于获取教务系统的Cookie
jwxt_url = "https://zhjw.nuc.edu.cn/jwglxt/xtgl/index_initMenu.html"
# 修改密码页面URL，当密码需要修改时会跳转到此页面
up_url = "http://zhrz.nuc.edu.cn:81/im/securitycenter/modifyPwd/index.zf"
# 实验教学管理平台测试URL，用于验证实验系统登录状态
experiment_test_url = "http://222.31.49.141/aexp/stuIndex.jsp"
# 实验教学管理平台登录URL
experiment_url = "http://sygl.nuc.edu.cn/aexp/stuIndex.jsp"
# 体育管理系统登录URL
physical_url = "https://zhrz.nuc.edu.cn/cas/login?" \
               "service=http%3A%2F%2Ftygl.nuc.edu.cn%2Fadmin%2Fmainzbsso%2Fadmin%2Flogin"
# 登录异常时的重定向URL，用于处理登录流程中的错误
e_login_url = "/cas/login?service=https%3A%2F%2Fzhmh.nuc.edu.cn%2F&exception.message=Error+decoding+flow+execution"
# 实验系统登录异常时的重定向URL
e_experiment_url = "/cas/login?service=http%3A%2F%2F222.31.49.141%2Fnuc%2F&" \
                   "exception.message=Error+decoding+flow+execution"
# 体育系统登录异常时的重定向URL
e_physical_url = "/cas/login?service=http%3A%2F%2Ftygl.nuc.edu.cn%2Fadmin%2Fmainzbsso%2Fadmin%2Flogin&" \
                 "exception.message=Error+decoding+flow+execution"
