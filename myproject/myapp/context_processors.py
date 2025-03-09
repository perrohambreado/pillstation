import time

def version(request):
    return {"VERSION": str(time.time())}

# grasias señor del stackoverflow