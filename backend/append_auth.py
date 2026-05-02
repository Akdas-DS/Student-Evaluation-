code = '''

@router.post("/reset-password")
def reset_password(data: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password_hash = auth.hash_password(data.new_password)
    db.commit()
    
    return {"detail": "Password successfully reset"}
'''

with open('c:/Desktop/Smart AI for students/backend/app/routers/auth_router.py', 'a', encoding='utf-8') as f:
    f.write(code)
print('Appended password reset route')
