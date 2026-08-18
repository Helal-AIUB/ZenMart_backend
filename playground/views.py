from django.shortcuts import render
from rest_framework.views import APIView
import logging
import requests

logger = logging.getLogger(__name__)

class HelloView(APIView):
    def get(self, request):
        data = {}  # ১. প্রথমে একটি ডিফল্ট ভ্যালু ডিক্লেয়ার করে নিলাম
        
        try:
            logger.info('calling httpbin')
            response = requests.get('https://httpbin.org/delay/2', timeout=5)
            logger.info('Received the response')
            
            # স্ট্যাটাস কোড ২০০ না হলে এটি এক্সেপশন থ্রো করবে
            response.raise_for_status()
            
            data = response.json()
            
        except requests.ConnectionError:
            logger.critical('httpbin is offline')
        except (requests.RequestException, ValueError) as e:
            # সার্ভার ডাউন থাকা বা 503 এরর কিংবা ভুল JSON আসলে এটি হ্যান্ডেল করবে
            logger.error(f'An error occurred: {e}')

        return render(request, 'hello.html', { 'name': 'Mosh', 'data': data })