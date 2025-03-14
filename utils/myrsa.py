import rsa


class Encrypt(object):
    def __init__(self, e, m):
        self.e = e
        self.m = m

    def encrypt(self, message):
        # 转换为十进制
        mm = int(self.m, 16)
        ee = int(self.e, 16)
        # 创建一个公钥对象
        rsa_pubkey = rsa.PublicKey(mm, ee)
        # 加密
        crypto = self._encrypt(message.encode(), rsa_pubkey)
        # 转换为16进制
        return crypto.hex()


    def _encrypt(self, message, pub_key):
        # 确定密钥长度
        keylength = rsa.common.byte_size(pub_key.n)
        # 根据密钥长度填充消息
        padded = self._pad_for_encryption(message, keylength)
        # 字符串转换为整数，因为加密需要整数
        payload = rsa.transform.bytes2int(padded)
        # 使用公钥的指数和模数执行 RSA 加密操作
        encrypted = rsa.core.encrypt_int(payload, pub_key.e, pub_key.n)
        # 加密后的结果转换回字符串，并返回
        block = rsa.transform.int2bytes(encrypted, keylength)

        return block

    # 用于对消息进行填充，以确保消息的长度和密钥长度一致
    '''为什么需要填充:
        1. 填充方式的定制化：加密算法通常需要对消息进行填充，以确保长度满足加密算法的要求。
        不同的填充方式可能会有不同的要求和处理逻辑。通过编写 _pad_for_encryption 方法，可以根据具体需求定制填充过程。
        2. 加密结果的格式转换：rsa 模块的加密函数通常返回字节串作为加密结果。
        但在特定的应用场景中，可能需要将加密结果表示为十六进制字符串或其他特定格式，以便于传输、存储或显示
    '''
    def _pad_for_encryption(self, message, target_length):
        # 颠倒顺序
        message = message[::-1]
        msglength = len(message)

        padding = b''
        # 算出需要填充的字节数，3是padding需要占用3个字节
        padding_length = target_length - msglength - 3

        for i in range(padding_length):
            padding += b'\x00'

        return b''.join([b'\x00\x00', padding, b'\x00', message])

# password = '%B7'
# print(Encrypt('10001', 'e9a315bf6d72428bf7d03d52f2f12418f3ed692703f572650d9f996b68be21fedb48805228619574a9df13393f6ea06ae929f64a88fd1edaf4489016caa5d779').encrypt(password[::-1]))