import time

def version(request):
    return {"VERSION": str(time.time())}

# grasias señol del stackoverflow