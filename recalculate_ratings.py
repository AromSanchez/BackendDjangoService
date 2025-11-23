from apps.services.models import Service
from apps.reviews.models import Review

def recalculate_ratings():
    print("Recalculating ratings for all services...")
    services = Service.objects.all()
    count = 0
    for service in services:
        reviews = Review.objects.filter(service=service, is_visible=True)
        reviews_count = reviews.count()
        if reviews_count > 0:
            rating_sum = sum(r.rating for r in reviews)
            rating_avg = rating_sum / reviews_count
            
            service.reviews_count = reviews_count
            service.rating_sum = rating_sum
            service.rating_avg = rating_avg
            service.save(update_fields=['reviews_count', 'rating_sum', 'rating_avg'])
            print(f"Updated service {service.id}: {rating_avg} ({reviews_count} reviews)")
            count += 1
        else:
            if service.reviews_count != 0 or service.rating_avg != 0:
                service.reviews_count = 0
                service.rating_sum = 0
                service.rating_avg = 0.0
                service.save(update_fields=['reviews_count', 'rating_sum', 'rating_avg'])
                print(f"Reset service {service.id} to 0")
                count += 1
                
    print(f"Done! Updated {count} services.")

if __name__ == '__main__':
    recalculate_ratings()
