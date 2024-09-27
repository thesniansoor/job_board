from datetime import date
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Applicant, Application, Company, Job, Notification
from django.utils import timezone
from django.core.paginator import Paginator
 
def login_user(request): 
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
 
        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, "accounts/login.html")
 
        user = authenticate(username=username, password=password)

        if user is not None: 
            try:
                applicant = Applicant.objects.get(user=user)
                if applicant.type == "applicant":
                    login(request, user)
                    return redirect("user_homepage")
            except Applicant.DoesNotExist:
                pass   

     
            try:
                company = Company.objects.get(user=user)
                if company.type == "company":
                    login(request, user)
                    return redirect("company_homepage")
            except Company.DoesNotExist:
                pass
 
            messages.error(request, "User type not recognized or invalid account.")
        else: 
            messages.error(request, "Invalid username or password.")

        return render(request, "accounts/login.html")
    
    return render(request, "accounts/login.html")



def logout_user(request):
    logout(request)
    return redirect('login')



def register_candidates(request):
    if request.method == "POST":   
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        gender = request.POST.get('gender')   
        image = request.FILES.get('image')   
 
        if not username or not first_name or not last_name or not email or not password1 or not password2 or not gender:
            messages.error(request, "All fields are required.")
            return redirect('register_candidates')
 
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register_candidates')
 
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register_candidates')
 
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken.")
            return redirect('register_candidates')
 
        user = User.objects.create_user(
            first_name=first_name, last_name=last_name,
            email=email, username=username, password=password1
        )

        applicants = Applicant.objects.create(user=user, gender=gender, image=image, type="applicant")
        user.save()
        applicants.save()

        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')

    return render(request, "accounts/register_candidates.html")

def register_company(request): 
    if request.method == "POST":   
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone') 
        company_name = request.POST.get('company_name')
        image = request.FILES.get('image')   
 
        if not username or not email or not first_name or not last_name or not password1 or not password2 or not phone or not company_name:
            messages.error(request, "All fields are required.")
            return redirect('register_company')
 
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register_company')
 
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register_company')
 
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken.")
            return redirect('register_company')

        #  company profile
        user = User.objects.create_user(
            first_name=first_name, last_name=last_name,
            email=email, username=username, password=password1
        )

        company = Company.objects.create(
            user=user, phone=phone, company_name=company_name,
            image=image, type="company", status="pending"
        )

        user.save()
        company.save()

        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')  

    return render(request, "accounts/register_company.html")


  
def home(request): 
    if request.user.is_authenticated:
        # Applicant
        try:
            applicant = Applicant.objects.get(user=request.user)
            if applicant: 
                query = request.GET.get('q')
                if query:
                    jobs = Job.objects.filter(title__icontains=query).order_by('-creation_date')  # Job search for candidates
                else:
                    jobs = Job.objects.all().order_by('-creation_date')[:5]  # Show all available jobs (limit to 5)
                return render(request, 'home.html', {'jobs': jobs, 'username': request.user.username, 'query': query})
        except Applicant.DoesNotExist:
            pass

        #   Company
        try:
            company = Company.objects.get(user=request.user)
            if company:
                query = request.GET.get('q')
                if query:
                    jobs = Job.objects.filter(title__icontains=query).order_by('-creation_date')  
                else:
                    jobs = Job.objects.all().order_by('-creation_date')[:5]  
                return render(request, 'home.html', {'jobs': jobs, 'username': request.user.username, 'query': query})
        except Company.DoesNotExist:
            pass
         
        return redirect("login") 
    else: 
        query = request.GET.get('q')
        if query:
            jobs = Job.objects.filter( 
                     title__icontains=query ,location__icontains=query).order_by('-creation_date')   
        else:
            jobs = Job.objects.all().order_by('-creation_date')[:5]   
            # featured_jobs = Job.objects.filter(featured=True)[:5]  
        return render(request, 'home.html', {'jobs': jobs, 'query': query})


 
def about(request):
    return render(request,"about.html")




# @login_required  # Only logged-in users can access this view
def contact(request):
    user_email = request.user.email  # Get the logged-in user's email
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')  # This will already be filled with the user's email
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if name and email and message:
            email_subject = f"New Contact Form Submission: {subject}"
            email_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

            try:
                # Send the email
                send_mail(
                    email_subject,  # Subject
                    email_message,  # Message
                    email,          # From user (their email)
                    ['thesni@mebron.com'],  # Admin email (your email)
                    fail_silently=False,
                )
                messages.success(request, "Your message has been sent successfully!")
                return redirect('contact')
            except Exception as e:
                messages.error(request, "An error occurred while sending the message. Please try again.")
        else:
            messages.error(request, "Please fill in all the fields.")
    
    return render(request, 'contact.html', {'user_email': user_email})





# def contact(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         email = request.POST.get('email')
#         subject = request.POST.get('subject')
#         message = request.POST.get('message')

#         # Prepare the email content
#         message_content = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

#         # Send the email using Django's send_mail
#         send_mail(
#             subject,
#             message_content,
#             settings.DEFAULT_FROM_EMAIL,  # From (admin's email)
#             [settings.DEFAULT_FROM_EMAIL],  # To (admin's email)
#             fail_silently=False,
#         )

#         # Add a success message and redirect
#         messages.success(request, 'Your message has been sent successfully!')
#         return redirect('contact')  # Redirect to the contact page

#     return render(request, 'contact.html')


def candidates(request):
    candidates = Applicant.objects.all()
    return render(request,"candidates.html", {'candidates': candidates})
 

def employers(request):
    companies = Company.objects.all() 
    context = {
        'companies': companies,
    }
    return render(request,"employers.html", {'companies': companies})


def company_vacancies(request, company_id):
    # Get the specific company
    company = get_object_or_404(Company, id=company_id)
    
    # Filter jobs associated with this company
    jobs = Job.objects.filter(company=company)
    
    # Pass the company and jobs to the template
    context = {
        'company': company,
        'jobs': jobs,
    }
    
    return render(request, 'company_vacancies.html', context)

def search_results(request):
    query = request.GET.get('q')
    jobs = Job.objects.all()
    companies = Company.objects.all()
    candidates = Applicant.objects.all()

    if query:
        jobs = jobs.filter(title__icontains=query)
        companies = companies.filter(company_name__icontains=query)
        candidates = candidates.filter(user__username__icontains=query)

    return render(request, 'search.html', {
        'jobs': jobs,
        'companies': companies,
        'candidates': candidates,
        'query': query
    })


 



# def job_listing(request):


#     if request.user.is_authenticated: 
#         try:
#             applicant = Applicant.objects.get(user=request.user)
#             if applicant: 
#                 query = request.GET.get('q')
#                 if query:
#                     jobs = Job.objects.filter(title__icontains=query).order_by('-creation_date')  
#                 else:
#                     jobs = Job.objects.all().order_by('-creation_date')  
#                 return render(request, 'job_listing.html', {'jobs': jobs, 'username': request.user.username, 'query': query})
#         except Applicant.DoesNotExist:
#             pass
 
#         try:
#             company = Company.objects.get(user=request.user)
#             if company:
#                 query = request.GET.get('q')
#                 if query:
#                     jobs = Job.objects.filter(company=company, title__icontains=query).order_by('-creation_date')   
#                 else:
#                     jobs = Job.objects.all().order_by('-creation_date')
#                 return render(request, 'job_listing.html', {'jobs': jobs, 'username': request.user.username, 'query': query})
#         except Company.DoesNotExist:
#             pass
         
#         return redirect("login")   
#     else: 
#         query = request.GET.get('q')
#         if query:
#             jobs = Job.objects.filter(title__icontains=query).order_by('-creation_date')  
#         else:
#             jobs = Job.objects.all().order_by('-creation_date') 


#     paginator = Paginator(job_list, 2)  # Show 10 jobs per page

#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)  # Get the requested page
 
#     return render(request, 'job_listing.html', {'jobs': jobs, 'query': query, 'page_obj': page_obj})

 
def job_listing(request):
    query = request.GET.get('q')
    
    # If user is authenticated
    if request.user.is_authenticated:
        try:
            # Applicant User
            applicant = Applicant.objects.get(user=request.user)
            if applicant:
                if query:
                    jobs = Job.objects.filter(title__icontains=query).order_by('-creation_date')
                else:
                    jobs = Job.objects.all().order_by('-creation_date')
        except Applicant.DoesNotExist:
            pass
        
        try:
            # Company User
            company = Company.objects.get(user=request.user)
            if company:
                if query:
                    jobs = Job.objects.filter(company=company, title__icontains=query).order_by('-creation_date')
                else:
                    jobs = Job.objects.all().order_by('-creation_date')
        except Company.DoesNotExist:
            pass

    else:
        # If user is not authenticated
        if query:
            jobs = Job.objects.filter(title__icontains=query).order_by('-creation_date')
        else:
            jobs = Job.objects.all().order_by('-creation_date')
 
    paginator = Paginator(jobs, 7)   
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)  

    return render(request, 'job_listing.html', {
        'page_obj': page_obj, 
        'query': query, 
        'username': request.user.username if request.user.is_authenticated else None
    })

def job_apply(request, myid): 
    if not request.user.is_authenticated:
        return redirect("login")
    
    applicant = Applicant.objects.get(user=request.user)
    job = get_object_or_404(Job, id=myid)
    date1 = date.today()

    # Check if the job is closed or not open yet
    if job.end_date < date1:
        closed = True
        return render(request, "job_apply.html", {'closed': closed})
    elif job.start_date > date1:
        notopen = True
        return render(request, "job_apply.html", {'notopen': notopen})
    
    # Check if the applicant has already applied for this job
    existing_application = Application.objects.filter(job=job, applicant=applicant).exists()
    if existing_application: 
        messages.error(request, "You have already applied for this job.")
        return render(request, "job_apply.html", {'job': job})

    # Handle POST request for job application
    if request.method == "POST": 
        # Check if resume is provided in the request
        if 'resume' not in request.FILES:
            messages.error(request, "All fields are required. Please upload your resume.")
            return render(request, "job_apply.html", {'job': job})

        # Get the resume from the uploaded files
        resume = request.FILES['resume']

        # Create a new application
        Application.objects.create(
            job=job,
            company=job.company,
            applicant=applicant,
            resume=resume,
            apply_date=date.today()
        )

        # Show success message and return response
        messages.success(request, "You have successfully applied for the job!")
        return render(request, "job_apply.html", {'alert': True, 'job': job})

    return render(request, "job_apply.html", {'job': job})

# def applied_jobs(request):
#     if request.user.is_authenticated:
#         try:
#             applicant = Applicant.objects.get(user=request.user)
#             applied_jobs = JobApplication.objects.filter(applicant=applicant).select_related('job').order_by('-application_date')
#             return render(request, 'admin/candidates/applied_jobs.html', {'applied_jobs': applied_jobs, 'username': request.user.username})
#         except Applicant.DoesNotExist:
#             # Handle case where the user is not an applicant
#             return redirect('login')
#     else:
#         return redirect('login')
    

def applied_jobs(request):
    if request.user.is_authenticated:
        try: 
            applicant = Applicant.objects.get(user=request.user)
             
            applied_jobs = Application.objects.filter(applicant=applicant).select_related('job').order_by('-apply_date')
           
            applied_jobs_count = applied_jobs.count()
             
            return render(request, 'admin/candidates/applied_jobs.html',   {
                           
                           'applied_jobs': applied_jobs, 
                           'applied_jobs_count': applied_jobs_count, 
                           'username': request.user.username
                           
                           })
        
        except Applicant.DoesNotExist:
            return redirect('login')
    else:
        return redirect('login')


def delete_applied_job(request, application_id):
    if request.user.is_authenticated:
        applicant = get_object_or_404(Applicant, user=request.user)        
        application = get_object_or_404(Application, id=application_id, applicant=applicant)   
        application.delete()     
        messages.success(request, "Application deleted successfully.")   
        return redirect('applied_jobs')
    else:
        return redirect('login')
# def all_applicants(request):
#     company = Company.objects.get(user=request.user)
#     application = Application.objects.filter(company=company)
#     return render(request, "admin/employers/all_applicants.html", {'application':application})    

def all_applicants(request):
    company = Company.objects.get(user=request.user)

    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        new_status = request.POST.get('status')
        application = get_object_or_404(Application, id=application_id, company=company)

        # Check if the application status has already been set
        # if application.status:
        #     messages.error(request, "The status for this application has already been updated and cannot be changed again.")
        #     return redirect('all_applicants')  # Redirect without making changes
 
        application.status = new_status
        application.save()

        # Send notification to the applicant
        applicant_user = application.applicant.user  
        if new_status == 'accepted':
            notification_message = f"Your application for   {application.job}  has been accepted."
            messages.success(request, notification_message)
        elif new_status == 'rejected':
            notification_message = f"Your application for   {application.job}  has been rejected."
            messages.warning(request, notification_message)
 
        Notification.objects.create(
            user=applicant_user,
            message=notification_message
        )

        return redirect('all_applicants')
 
    application_list = Application.objects.filter(company=company)

    return render(request, "admin/employers/all_applicants.html", {
        'application': application_list,
    })



def delete_applicant(request, id):
    application = get_object_or_404(Application, id=id)
    
    if request.method == 'POST':
        application.delete()
        messages.success(request, "Application deleted successfully.")
        return redirect('all_applicants')  

    return redirect('all_applicants')  



# def all_applicants(request, id):
#     # Get the job application by ID or return 404 if not found
#     job_application = get_object_or_404(JobApplication, id=id)

#     if request.method == 'POST':
#         # Get the status from the form data
#         status = request.POST.get('status')

#         # Check if the status is valid
#         if status in ['accepted', 'rejected']:
#             # Update the status of the job application
#             job_application.status = status
#             job_application.save()

#             # Reload the same page with a success message
#             return render(request, 'admin/employers/all_applicants.html', {
#                 'job_application': job_application,
#                 'application': JobApplication.objects.all(),  # Or other context needed
#                 'success': f"Status updated to {status}."
#             })
    
#     # If it's a GET request, just render the page normally
#     return render(request, 'admin/employers/all_applicants.html', {
#         'job_application': job_application,
#         'application': JobApplication.objects.all()
#     })

 


 #company 

def company_homepage(request):
       # Assuming each user has one company, get the company related to the logged-in user
    if request.user.is_authenticated:
        # Get the company for the authenticated user
        company = Company.objects.get(user=request.user)
        
        context = {
            'company': company,  # Pass the company to the template
        }
        return render(request, 'admin/employers/company_homepage.html', context)
    else:
        return redirect('login')  # Redirect to login if not authenticated


def company_profile(request):
    if not request.user.is_authenticated:
        return redirect("login")
    company = Company.objects.get(user=request.user)
    if request.method=="POST":   
        company_name = request.POST['company_name']
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        phone = request.POST['phone'] 
        description = request.POST['description']
        website = request.POST['website']
        
 
        company.company_name = company_name
        company.user.first_name = first_name
        company.user.last_name = last_name
        company.phone = phone  
        company.description = description
        company.website = website
        company.save()
        company.user.save()
 
        try:
            image = request.FILES['image']
            company.image = image
            company.save()
        except:
            pass
        alert = True
        # return render(request, "admin/employers/company_profile.html", {'alert':alert})
        return redirect('company_profile') 
    return render(request, "admin/employers/company_profile.html", {'company':company})




def add_job(request):
    if not request.user.is_authenticated:
        return redirect("login")       
    if request.method == "POST":
        title = request.POST['job_title']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        salary = request.POST['salary']
        image = request.FILES['logo']
        experience = request.POST['experience']
        location = request.POST['location']
        skills = request.POST['skills']
        description = request.POST['description'] 
        
        job_type = request.POST['job-Type']  
        work_location = request.POST['Work-location']   

        user = request.user
        company = Company.objects.get(user=user)
        job = Job.objects.create(company=company, title=title,start_date=start_date, end_date=end_date, salary=salary, 
                                 image=image, experience=experience, location=location, skills=skills, description=description,job_type=job_type,
                                 work_location=work_location, creation_date=date.today())
        job.save()
        messages.success(request, 'Job added successfully!') 
   
        alert = True
        return render(request, "admin/employers/add_job.html", {'alert':alert}) 
     
    return render(request, "admin/employers/add_job.html")



def edit_job(request, myid):
    if not request.user.is_authenticated:
        return redirect("/company_login")
    
    job = Job.objects.get(id=myid)
    
    if request.method == "POST":
        title = request.POST['job_title']
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        salary = request.POST['salary']
        experience = request.POST['experience']
        location = request.POST['location']
        skills = request.POST['skills']
        description = request.POST['description']
        job_type = request.POST['job-Type']
        work_location = request.POST['Work-location']

 
        job.title = title
        job.salary = salary
        job.experience = experience
        job.location = location
        job.skills = skills
        job.description = description
        job.job_type = job_type
        job.work_location = work_location
        job.save()
        messages.success(request, 'Job edited successfully!') 

        if start_date:
            job.start_date = start_date
            job.save()

        if end_date:
            job.end_date = end_date
            job.save()

       
        try:
            image = request.FILES['image']
            job.image = image
            job.save()
        except KeyError:
            pass

        return redirect('edit_job', myid=myid)   

    return render(request, "admin/employers/edit_job.html", {'job': job})



def job_details(request, myid):
    job = Job.objects.get(id=myid)
    return render(request,"job_details.html", {'job':job})

  
def job_list(request):
    if not request.user.is_authenticated:
        return redirect("login")
    companies = Company.objects.get(user=request.user)
    jobs = Job.objects.filter(company=companies)
    return render(request, "admin/employers/job_list.html", {'jobs':jobs})

def job_detail(request, myid):
    job = Job.objects.get(id=myid)
    return render(request, "admin/employers/job_detail.html", {'job':job})

def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted successfully.")
        return redirect('job_list')  

    return redirect('job_list')





#  User Candidate

def user_homepage(request):
    if not request.user.is_authenticated:
        return redirect('login/')

    # Fetch unread notifications for the logged-in user
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')

    return render(request, "admin/candidates/user_homepage.html", {
        'notifications': notifications,
    })


def notification(request):
    if not request.user.is_authenticated:
        return redirect('login/')
    
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    
    return render(request,"admin/candidates/notification.html" , {
        'notifications': notifications,
    })

# def user_homepage(request):
#     if not request.user.is_authenticated:
#         return redirect('/login/')

#     # Get the logged-in applicant
#     applicant = get_object_or_404(Applicant, user=request.user)

#     return render(request, "admin/candidates/user_homepage.html", {
#         'applicant': applicant,  # Pass the applicant instance if needed
#         'messages': messages.get_messages(request),  # Pass messages to the template
#     })

def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('/login/') 
    
    applicant = Applicant.objects.get(user=request.user)

    if request.method=="POST":   
        email = request.POST['email']
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        phone = request.POST['phone']
        gender = request.POST['gender']
        work = request.POST['work']
        year = request.POST['year']
        education_level = request.POST['education_level']
        
 
        applicant.user.email = email
        applicant.user.first_name = first_name
        applicant.user.last_name = last_name
        applicant.phone = phone
        applicant.gender = gender
        applicant.work = work
        applicant.year = year
        applicant.education_level = education_level
        applicant.save()
        applicant.user.save()
 
        try:
            image = request.FILES['image']
            applicant.image = image
            applicant.save()
        except:
            pass
        alert = True 
        
        messages.success(request, 'Your form was successfully submitted!')
   
        # messages.error(request, 'There was an error processing your request.')
        # return render(request, "admin/candidates/user_profile.html", {'alert':alert})
 
        return redirect('user_profile')  

    
    return render(request, "admin/candidates/user_profile.html", {'applicant':applicant})









# @login_required(login_url='login') 
# def job_seeker_dashboard(request):
#     return render(request,"admin/job_seeker_dashboard.html")

 



# def employer_dashboard(request):
#     return render(request,"admin/employers/employer_dashboard.html")

# def company_profile(request):
#     return render(request,"admin/employers/company_profile.html")

# def add_job(request):
#     return render(request,"admin/employers/add_job.html")   

# def edit_job(request):
#     return render(request,"admin/employers/edit_job.html")   

# def startup(request):
#     return render(request,"admin/employers/startup.html")  









# #candidate

# def job_seeker_dashboard(request):
#     return render(request,"admin/candidates/job_seeker_dashboard.html") 

# def my_applied(request):
#     return render(request,"admin/candidates/my_applied.html") 

# def my_profile(request):
#     return render(request,"admin/candidates/my_profile.html") 

# def add_profile(request):
#     return render(request,"admin/candidates/add_profile.html") 

# def edit_profile(request):
#     return render(request,"admin/candidates/edit_profile.html") 