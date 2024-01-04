# pwd.py - Script to create user and handle passwords
#
# Date: 20210607
# Author(s): Philip

# Import dependencies
from string import ascii_letters, digits
from secrets import token_bytes, choice
from hashlib import pbkdf2_hmac

# Check if entered passwords are identical
def pwd_id(pwd_a, pwd_b):
	return pwd_a == pwd_b	 

# Check if entered password is between 8 and 24 characters inclusive
def pwd_len(password):
	return password and len(password) >= 8 and len(password) <= 1024

# Generate a key for the API
def api_key(size):
	alphabet = ascii_letters + digits
	#sanitized_alphabet = "bcdfghjkmpqrtvwxyBCDFGHJKMPQRTVWXY346789" # Used by Microsoft
	return ''.join(choice(alphabet) for i in range(size))

# Generate a salt as a 32 random bytes
def pwd_salt():
	return token_bytes(32)

# Generate the key to store by adding salt to passowrd and hashing
def pwd_hash(password, salt=b''):
	key = pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000, 64)
	return key

def pwd_check(password, key, salt=b''):
	return key == pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000, 64)

# Function for running tests
def _test():
	test_largepwd1 = "+Q!M6bYa9uj@m%9XNp+JAsSZZKZ=?D9Bm8R7bL6xXSkxGuy4BJ2AKbwN#bW7M8+=Q5xLPYsSR^WC%XA76%KeG^yG8u=YCGYgLKcRFwN!Pb-VZpzzfsqVbJZDm=z^ra*QxtD+Z99-aRMT3+?xBk!n#*uNUUzgTn93+NXWn^Guvpev+Ac@PxXX5AKCBA^ZWZZSLy!SQv=2Bg8h8P8G=p7vY7@j+V!y8nt#42MT%WzzuRvmBfYn9t=YePNgSFXyM4e2sgFBEJaSXw!cS7KjqYXLe^&jmd?@*kj@w93@fSfSg%bq?@4PGedZnn=EBYhm?!_AwEw^66nC+WmS3db*eqJM^2HQ-nMu6whw79A!uKPtwp35D_39r-g4$cQy*myn?_wP%ud-Quh!B$dPjrgF4Qk9ZJLs3p9L4BCDzLt2PJxr&5R*RFUQZMdzv!mF#EL5m3uTLb+*yFSY#=^PPfx&HxSNNw&Lk9mkT7kPaUJ9kpyxSBCD*#8gfM6J%QK__Teqjg*AtRszC-mvMxcZ8JEDTab-zbpN%ApXFegvS+Dhy6efrFPPaRE+rSQRQdFGm4YS@4j-v5NkWF@KERu##YHeAYVU_CqtJ5KTG3?&BFSb3GXeTJjXbSL2Pem58fmLn2=Jsyzw8vXLWjV*Nw_gr&2AWF*k+5G*Pn_gr+n&wug9#4AfHnRhdMmKtcp#MEzWBfMJ=u#XyD$qHWsNyGbHfMDVuT9_82xc!_TAt=c-2CNpTmz*UxDdJ@+2Xt2X4zTSH=G7fGLd+N%kE8JkgS=MswAsX@gv-jvm?yW&@#szf3^&Sv@%cvxtMfVGf?N784y#!r@kApRt4nb@t@=nH@cD?Egr28ATjvtK#fdKc!wfrMH5#YSxA&M7Zzt5J^%64jCHyRdJEAmK-ywnj9jp_BgwYFMhGyFMk+mes3Qyc76ysBpgrU+tFx2-am9?8Lq4W+pgEG++MW9Y7y-XBAfrP=hyrgJnvkSm9!?q+#H=Dqw3gYMC_4GwYA35L?MUzM2hQ?dT$L36V$DU"
	test_largepwd2 = "+#Q!M6bYa9uj@m%9XNp+JAsSZZKZ=?D9Bm8R7bL6xXSkxGuy4BJ2AKbwN#bW7M8+=Q5xLPYsSR^WC%XA76%KeG^yG8u=YCGYgLKcRFwN!Pb-VZpzzfsqVbJZDm=z^ra*QxtD+Z99-aRMT3+?xBk!n#*uNUUzgTn93+NXWn^Guvpev+Ac@PxXX5AKCBA^ZWZZSLy!SQv=2Bg8h8P8G=p7vY7@j+V!y8nt#42MT%WzzuRvmBfYn9t=YePNgSFXyM4e2sgFBEJaSXw!cS7KjqYXLe^&jmd?@*kj@w93@fSfSg%bq?@4PGedZnn=EBYhm?!_AwEw^66nC+WmS3db*eqJM^2HQ-nMu6whw79A!uKPtwp35D_39r-g4$cQy*myn?_wP%ud-Quh!B$dPjrgF4Qk9ZJLs3p9L4BCDzLt2PJxr&5R*RFUQZMdzv!mF#EL5m3uTLb+*yFSY#=^PPfx&HxSNNw&Lk9mkT7kPaUJ9kpyxSBCD*#8gfM6J%QK__Teqjg*AtRszC-mvMxcZ8JEDTab-zbpN%ApXFegvS+Dhy6efrFPPaRE+rSQRQdFGm4YS@4j-v5NkWF@KERu##YHeAYVU_CqtJ5KTG3?&BFSb3GXeTJjXbSL2Pem58fmLn2=Jsyzw8vXLWjV*Nw_gr&2AWF*k+5G*Pn_gr+n&wug9#4AfHnRhdMmKtcp#MEzWBfMJ=u#XyD$qHWsNyGbHfMDVuT9_82xc!_TAt=c-2CNpTmz*UxDdJ@+2Xt2X4zTSH=G7fGLd+N%kE8JkgS=MswAsX@gv-jvm?yW&@#szf3^&Sv@%cvxtMfVGf?N784y#!r@kApRt4nb@t@=nH@cD?Egr28ATjvtK#fdKc!wfrMH5#YSxA&M7Zzt5J^%64jCHyRdJEAmK-ywnj9jp_BgwYFMhGyFMk+mes3Qyc76ysBpgrU+tFx2-am9?8Lq4W+pgEG++MW9Y7y-XBAfrP=hyrgJnvkSm9!?q+#H=Dqw3gYMC_4GwYA35L?MUzM2hQ?dT$L36V$DU"
	test_pwd = "Happydays12"
	test_salt = pwd_salt()
	test_key = pwd_hash(test_pwd, test_salt)
	assert pwd_check(test_pwd, test_key, test_salt), "Password and key are equal"
	assert len(test_key) == 64, "Password key is of length 64"
	assert pwd_id("graduation", "graduation"), "Password is identical"
	assert not pwd_id("Homecoming", "homecoming"), "Password is not identical"
	assert not pwd_len("Sunny"), "Password is a too short."
	assert not pwd_len(test_largepwd2), "Password is too long"
	assert pwd_len(test_largepwd1), "Password is correct length"
	assert len(pwd_hash(test_largepwd1 , test_salt)) == 64, "1024 password has a key length 64"

if __name__ == '__main__':
	_test()