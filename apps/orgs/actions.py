from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .services import accept_invitation

class AcceptInvitationView(LoginRequiredMixin, View):
    def get(self, request, token):
        success, message = accept_invitation(token, request.user)
        if success:
            return redirect('events:list')
        else:
            return render(request, 'orgs/invitation_error.html', {'message': message})
