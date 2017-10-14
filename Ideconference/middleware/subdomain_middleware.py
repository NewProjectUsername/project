class SubdomainMiddleware(object):
    def process_request(self, request):
        try:
            url_elements = request.META['HTTP_HOST'].split('.')
            if len(url_elements) >= 3:
                request.subdomain = url_elements[0]
                print("poddomena", request.subdomain)
            else:
                request.subdomain = None
                print("brez poddomene")
        except KeyError:
            print("KeyError")
            request.subdomain = None
