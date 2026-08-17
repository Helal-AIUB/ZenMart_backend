# from django.core.mail import EmailMessage ,send_mail, mail_admins, BadHeaderError
# from templated_mail.mail import BaseEmailMessage
from django.shortcuts import render
from .tasks import notify_customers



# Create your views here.


def say_hello(request):
    notify_customers.delay('Hello')

    return render(request, 'hello.html', { 'name':'Mohsin' })

    # try:
    #     message = BaseEmailMessage(
    #         template_name = 'emails/hello.html',
    #         context = {'name': 'Mosh'}
    #     )
    #     message.send(['john@moshbuy.com'])

    # except BadHeaderError:
    #     pass
