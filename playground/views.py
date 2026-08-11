from django.core.mail import EmailMessage ,send_mail, mail_admins, BadHeaderError
from django.shortcuts import render
from templated_mail.mail import BaseEmailMessage


# Create your views here.


def say_hello(request):
    try:
        message = BaseEmailMessage(
            template_name = 'emails/hello.html',
            context = {'name': 'Mosh'}
        )
        message.send(['john@moshbuy.com'])

        # message = EmailMessage('subject', 'message', 'from@moshbuy.com', ['john@moshbuy.com'])
        # message.attach_file('playground/static/images/cat1.jpg')
        # message.send()

        # mail_admins('subject', 'message', html_message='message')

        # send_mail('subject', 'message', 'info@moshbuy.com', ['bob@moshbuy.com'])
    except BadHeaderError:
        pass
    return render(request, 'hello.html', { 'name':'Mohsin' })
