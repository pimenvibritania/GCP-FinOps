from rest_framework import status

class UnprocessableEntityException():
  def __init__(self, message):
    self.message = {
      "success": False, 
      "message": message
    }
    self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

class BadRequestException():
  def __init__(self, message):
    self.message = {
      "success": False, 
      "message": message
    }
    self.status_code = status.HTTP_400_BAD_REQUEST

class UnauthenticatedException():
  def __init__(self, message):
    self.message = {
      "success": False, 
      "message": message
    }
    self.status_code = status.HTTP_401_UNAUTHORIZED

class UnauthorizedException():
  def __init__(self, message):
    self.message = {
      "success": False, 
      "message": message
    }
    self.status_code = status.HTTP_403_FORBIDDEN