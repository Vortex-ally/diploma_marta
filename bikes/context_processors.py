from velos.bikes.cart import cart_count


def cart_context(request):
    return {'cart_count': cart_count(request.session)}

