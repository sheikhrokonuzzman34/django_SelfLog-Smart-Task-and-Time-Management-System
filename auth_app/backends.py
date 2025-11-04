# from django.contrib.auth.backends import ModelBackend
# from django.contrib.auth import get_user_model
# from django.db.models import Q

# class EmailOrPhoneBackend(ModelBackend):
#     """Custom authentication backend allowing email or phone number login"""
    
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         UserModel = get_user_model()
        
#         if username is None:
#             username = kwargs.get(UserModel.USERNAME_FIELD)
        
#         try:
#             # Try to find user by email or phone number
#             user = UserModel.objects.get(
#                 Q(email=username) | 
#                 Q(phone_number=username)
#             )
#         except UserModel.DoesNotExist:
#             # Run the default password hasher once to reduce timing difference
#             UserModel().set_password(password)
#             return None
#         except UserModel.MultipleObjectsReturned:
#             # This should not happen if email and phone are unique
#             return None
        
#         if user.check_password(password) and self.user_can_authenticate(user):
#             # Track login method
#             if '@' in username:
#                 user.last_login_method = 'email'
#             else:
#                 user.last_login_method = 'phone'
#             user.save(update_fields=['last_login_method'])
#             return user
        
#         return None