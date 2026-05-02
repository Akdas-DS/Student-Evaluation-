code = '''

class PasswordResetRequest(BaseModel):
    email: str
    new_password: str = Field(..., min_length=8)
'''

with open('c:/Desktop/Smart AI for students/backend/app/schemas.py', 'a', encoding='utf-8') as f:
    f.write(code)
print('Appended schema')
