# Create your views here./
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth import authenticate, login as auth_login
from django.template import Context, loader
from django.template import RequestContext
from django.shortcuts import render_to_response
from members.forms import *
from members.models import *
from datetime import datetime  
from django.shortcuts import redirect
from django.conf import settings
import braintree
import time


client_side_key = settings.BRAINTREE_CLIENT_KEY

def validateEmail( email ):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False

def render_subscription(request,messages):

    braintree_customer              = None 
    braintree_plans                 = None
    braintree_customer_subscription = None
    customer_cards                  = None

    braintree_model = BrainTree()

    try:
        braintree_plans     = braintree.Plan.all() 
    except Exception,ex:
        f = open('/tmp/braintree_getcustomer','a')
        f.write(repr(ex))
        f.close()


    try:
        braintree_customer  = braintree_model.get_braintree_customer(str(request.user.id))
    except Exception,ex:
        f = open('/tmp/braintree_getcustomer','a')
        f.write(repr(ex))
        f.close()

    if request.user.subscription_code is not None and request.user.subscription_code != '' and hasattr(request.user, 'subscription_code'):
        braintree_customer_subscription = braintree_model.get_subscription(request.user.subscription_code)


    if braintree_customer is not None and hasattr(braintree_customer, 'credit_cards'):
        customer_cards = braintree_customer.credit_cards


    variables = RequestContext(request,{
                                        'subscription'      : braintree_customer_subscription,
                                        'info_messages'     : messages['info_messages'],
                                        'success_messages'  : messages['success_messages'],
                                        'error_messages'    : messages['error_messages'],
                                        'client_side_key'   : client_side_key,
                                        'cards'             : customer_cards,
                                        'plans'             : braintree_plans,
                                        }
                             )

    return render_to_response('payment/recurring_billing.html', variables)






def index(request):

    if request.user.is_authenticated():
        request.session.modified = True
        if request.user.member_level.level >= 50:
            page_data = {'user':request.user}
            variables = RequestContext(request, page_data)
            return render_to_response('members/index.html', variables)
        else:
            page_data = {
                    'user':request.user,
                    'message':'Thank you for registering your account needs to be approved before you can become a member. Please come down to one of our meetings and hang out in irc http://webchat.freenode.net/ #dc801 chat.freenode.net or www.dc801.org. On Freenode #dc801 ask for Nemus, L34n or Metacortex for more information.'
                    }
            variables = RequestContext(request,page_data)
            return render_to_response('members/index.html', variables)

    return render_to_response('members/index.html', RequestContext(request))


def subscriptions(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    if not request.user.member_level.level >= 50:
        return HttpResponseRedirect('/')

    request.session.modified = True
    braintree_model = BrainTree()

    #info_messages       = []
    #error_messages      = []
    #success_messages    = []
    
    messages = {}
    messages['info_messages']       = [];
    messages['error_messages']      = [];
    messages['success_messages']    = [];

    braintree_customer              = None 
    braintree_plans                 = None
    braintree_customer_subscription = None
    customer_cards                  = None

    #try:
        #braintree_plans     = braintree.Plan.all() 
        #braintree_customer  = braintree_model.get_braintree_customer(str(request.user.id))

    #except Exception,ex:
    #    f = open('/tmp/braintree_getcustomer','a')
    #    f.write(repr(ex))
    #    f.close()

    message = ''
    cards = None

    #braintree_customer  = braintree_model.get_braintree_customer(str(request.user.id))
    #if braintree_customer is not None and hasattr(braintree_customer, 'credit_cards'):
    #    customer_cards = braintree_customer.credit_cards

    #if request.user.subscription_code is not None and request.user.subscription_code != '' and hasattr(request.user, 'subscription_code'):
    #    braintree_customer_subscription = braintree_model.get_subscription(request.user.subscription_code)



    if request.method == 'POST':


        if request.POST['method'] == 'delete_card':
        
            if 'delete_token' not in request.POST or len(request.POST['delete_token']) < 1 :
                    error_message = "Cannot delete card invalid token sent."
                    messages['error_messages'].append(error_message)
                    #render
                    return render_subscription(request,messages)

            #get card token from request
            delete_card_token = request.POST['delete_token'].strip()
            
            #get subscriptions so we we can compair card tokens
            if request.user.subscription_code is not None and request.user.subscription_code != '' and hasattr(request.user, 'subscription_code'):
                braintree_customer_subscription = braintree_model.get_subscription(request.user.subscription_code)

            if braintree_customer_subscription is not None:
        
                if braintree_customer_subscription.payment_method_token == delete_card_token:

                    error_message = "Cannot delete card tied to subscription \""+braintree_customer_subscription.plan_id+"\". Please cancel subscription first."
                    messages['error_messages'].append(error_message)
                    #render
                    return render_subscription(request,messages)
                    

            delete_card_response = braintree_model.delete_card(delete_card_token)
                
            if delete_card_response.is_success:
                success_message = "Succesfully deleted card. "
                messages['success_messages'].append(success_message)

                #render
                return render_subscription(request,messages)
                
            else:
                error_message = "Could not delete card. "
                messages['error_messages'].append(error_message)
                return render_subscription(request,messages)

        if request.POST['method'] == 'cancel':

            #get subscription
            if request.user.subscription_code is not None and request.user.subscription_code != '' and hasattr(request.user, 'subscription_code'):
                braintree_customer_subscription = braintree_model.get_subscription(request.user.subscription_code)

            if braintree_customer_subscription is not None:

                cancel_result = braintree_model.cancel_subscription(braintree_customer_subscription.id)
                if cancel_result.is_success:

                    info_message = "Old Subscription \""+braintree_customer_subscription.plan_id+"\" Canceled. "
                    messages['info_messages'].append(info_message)

                    request.user.subscription_code = None
                    request.user.save()
                    braintree_customer_subscription = None

                    return render_subscription(request,messages)

                else:
                    info_message =  "Old Subscription was NOT \""+braintree_customer_subscription.plan_id+"\" Canceled please call (385) 313-0801 and leave a voicemail. "
                    messages['info_messages'].append(info_message)

                    return render_subscription(request,messages)
            else:
                info_message = "You do not have a Subcription to Cancel. "
                messages['info_messages'].append(info_message)

                return render_subscription(request,messages)
 

        if request.POST['method'] == 'subscribe':

            subscribe_error = False

            if 'card_token' not in request.POST or len(request.POST['card_token']) < 1:
                    error_message = "Cannot create subscription invalid card token."
                    messages['error_messages'].append(error_message)
                    subscribe_error = True
                    

            if 'plan_id' not in request.POST or len(request.POST['plan_id']) < 1:
                    error_message = "Cannot create subscriptions user card invalid plan_id."
                    messages['error_messages'].append(error_message)
                    subscribe_error = True
                

            if subscribe_error:
                    return render_subscription(request,messages)

            #get data
            card_token = request.POST['card_token'].strip()
            plan_id    = request.POST['plan_id'].strip()


            if request.user.subscription_code is not None and request.user.subscription_code != '' and hasattr(request.user, 'subscription_code'):
                braintree_customer_subscription = braintree_model.get_subscription(request.user.subscription_code)

            if braintree_customer_subscription is not None:

                    error_message = "Please cancel subscription \""+braintree_customer_subscription.plan_id+"\" before creating a new one. "
                    messages['error_messages'].append(error_message)
                    return render_subscription(request,messages)
 
            else:

                subscription_response = braintree_model.set_subscriptions(card_token,plan_id)

                if subscription_response.is_success:

                        request.user.subscription_code = subscription_response.subscription.id
                        request.user.save()

                        braintree_customer_subscription  = subscription_response.subscription
                        success_message     = message +  " New Subscription \""+subscription_response.subscription.plan_id+"\" Successful Set"
                        messages['success_messages'].append(success_message)

                        return render_subscription(request,messages)
     

                else:
                        error_message = 'Setting Subscription Failed'
                        messages['error_messages'].append(error_message)
                        return render_subscription(request,messages)
 

        if request.POST['method'] == 'addcard':

            #f = open('/tmp/addcard','a')
            #f.write(repr(request.POST)) 
            #f.close()

            addcard_error = False

            if 'first_name' not in request.POST:
                addcard_error = True
                error_message     = 'Failed adding card "First Name" is invalid.'
                messages['error_messages'].append(error_message)

            if 'last_name' not in request.POST:
                addcard_error = True
                error_message     = 'Failed adding card "Last Name" is invalid.'
                messages['error_messages'].append(error_message)

            if 'postal_code' not in request.POST or not re.match(r'^\d{5}([\-]?\d{4})?$', request.POST['postal_code'].strip()):
                addcard_error = True
                error_message     = 'Failed adding card "Postal Code" is invalid.'
                messages['error_messages'].append(error_message)
             
            if 'account' not in request.POST:
                addcard_error = True
                error_message     = 'Failed adding card "Account" is invalid.'
                messages['error_messages'].append(error_message)

            if 'month' not in request.POST:
                addcard_error = True
                error_message     = 'Failed adding card "Month" is invalid.'
                messages['error_messages'].append(error_message)

            if 'year' not in request.POST:
                print request.POST['year'].strip()
                addcard_error = True
                error_message     = 'Failed adding card "Year" is invalid.'
                messages['error_messages'].append(error_message)

            if 'cvv' not in request.POST:
                addcard_error = True
                error_message     = 'Failed adding card "CVV" is invalid.'
                messages['error_messages'].append(error_message)
          

            if addcard_error:
                return render_subscription(request,messages)

            first_name  = request.POST['first_name'].strip()
            last_name   = request.POST['last_name'].strip()
            postal_code = request.POST['postal_code'].strip()
            account     = request.POST['account'].strip()
            month       = request.POST['month'].strip()
            year        = request.POST['year'].strip()
            cvv         = request.POST['cvv'].strip()
            user_id     = request.user.id


            try:
                braintree_customer  = braintree_model.get_braintree_customer(str(request.user.id))
            except Exception,ex:
                f = open('/tmp/braintree_getcustomer','a')
                f.write(repr(ex))
                f.close()

            if braintree_customer is None:

                customer = { 'first_name'  : first_name,
                             'last_name'   : last_name,
                             'postal_code' : postal_code,
                             'account'     : account,
                             'month'       : month,
                             'year'        : year,
                             'cvv'         : cvv,
                             'id'          : user_id,
                            }

                customer_result = braintree_model.create_customer(customer)

                if customer_result is not None and customer_result.is_success:

                    success_message     = 'Adding a new card was succesful.'
                    messages['success_messages'].append(success_message)
                    return render_subscription(request,messages)

                else:
                    error_message     = 'Adding a new card failed customer.'
                    messages['error_messages'].append(error_message)
                    return render_subscription(request,messages)
            else:
                addcard = {'customer_id'     :  user_id,
                            'account'        :  account,
                            'month'          :  month,
                            'year'           :  year,
                            'first_name'     :  first_name,
                            'last_name'      :  last_name,
                            "cvv"            :  cvv,
                            }

                addcard_result = braintree_model.addcard_to_customer(addcard)

                #f = open('/tmp/addcard_result','a')
                #f.write(repr(addcard_result))
                #f.close()

                if addcard_result.is_success:

                    success_message     = 'Adding a new card was succesful.'
                    messages['success_messages'].append(success_message)
                    return render_subscription(request,messages)

                else:
                    error_message     = 'Adding a new card failed.'
                    messages['error_messages'].append(error_message)
                    return render_subscription(request,messages)

    return render_subscription(request,messages)


def payment(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    if not request.user.member_level.level >= 50:
        return HttpResponseRedirect('/')

    request.session.modified = True
    if request.method == 'POST':
        
        account  = ''
        cvv      = ''
        month    = ''
        year     = ''
        amount   = ''

        braintree_model = BrainTree()
        data = request.POST

        error = False 
        error_message = ''
        if 'number' in data:
            pass
        else:
            error = True
            error_message = error_message + 'Account Number is Required. ' 
        if 'cvv' in data:
            pass
        else:
            error = True
            error_message = error_message + 'CVV is Required. '

        if 'payment_level' in data:
            pattern = r'^[1-9]{1}$'
            result = re.match(pattern, data['payment_level'].strip())
            print data['payment_level']
            if result:
                if data['payment_level'] == '1':
                    amount = '50.00'
                elif data['payment_level'] == '2':
                    amount = '75.00'
                elif data['payment_level'] == '3':
                    amount = '100.00'
                elif data['payment_level'] == '4':
                    amount = '200.00'
                elif data['payment_level'] == '5':
                    amount = '25.00'
                elif data['payment_level'] == '6':
                    amount = '300.00'
                elif data['payment_level'] == '7':
                    amount = '600.00'
                elif data['payment_level'] == '8':
                    amount = '450.00'
                elif data['payment_level'] == '9':
                    amount = '900.00'
             
                else:
                    error = True
                    error_message = error_message + ' Payment Level is invalid. '
            else:
                error = True
                error_message = error_message + ' Amount is Invalid. ' 
        
        else:
            error = True
            error_message = error_message + ' Amount is Required. ' 
        if 'year' in data:
            pattern = r'^[0-9]{4}$'
            result = re.match(pattern, data['year'].strip())
            if result:
                pass
            else:
                error = True
                error_message = error_message + 'Year is Invalid. ' 
        else:
            error = True
            error_message = error_message + 'Year is Required. ' 
        if 'month' in data:
            pattern = r'^[0-9]{2}$'
            result = re.match(pattern, data['month'].strip())
            if result: 
                pass
            else:
                error = True
                error_message = error_message + 'Month is Invalid. '
        else:
            error = True
            error_message = error_message + 'Month is Required. ' 

        if error:
            variables = RequestContext(request, {'message':error_message,'client_side_key':client_side_key})
            return render_to_response('payment/singlepayment.html', variables)
   

        account  = request.POST['number'].strip()
        cvv      = request.POST['cvv'].strip()
        month    = request.POST['month'].strip()
        year     = request.POST['year'].strip()

        payment     = { 'account'   :account,
                        'cvv'       :cvv,
                        'month'     :month,
                        'year'      :year,
                        'amount'    :amount,
                        }
        
        transaction = braintree_model.create_transaction(payment,request.user)

        if transaction is not None and transaction.success:
            message = 'Transaction Succesful'
            variables = RequestContext(request, {'message':message,'amount':payment['amount'],'transaction_id':transaction.id})
            return render_to_response('payment/singlepaymentsuccessful.html', variables)

        else:
            message = 'Sorry your transaction FAILED please try again'
            variables = RequestContext(request, {'message':message,'client_side_key':client_side_key})
            return render_to_response('payment/singlepayment.html', variables)

    variables = RequestContext(request,{'client_side_key':client_side_key})
    return render_to_response('payment/singlepayment.html', variables)

def login(request):

    if request.user.is_authenticated():
        return render_to_response('members/index.html', RequestContext(request))

    if request.method == 'POST':
        request.session.modified = True    
        form = LoginForm(request.POST)
        if not form.is_valid():
            message = "Registration failed please try again."
            form = LoginForm()
            variables = RequestContext(request, {'form': form,'message':message})
            return render_to_response('registration/login.html',variables)


        u_email     = request.POST['email']
        u_password  = request.POST['password']

        if validateEmail(u_email):
            try:
                user = DC801User.objects.get(email=u_email)
            except DC801User.DoesNotExist:
                 message = "Your username or password is incorrect."
                 form = LoginForm()
                 variables = RequestContext(request, {'form': form,'message':message})
                 return render_to_response('registration/login.html',variables)
        else:
            message = "Your username or password is incorrect."
            form = LoginForm()
            variables = RequestContext(request, {'form': form,'message':message})
            return render_to_response('registration/login.html',variables)

        if user.is_active:
            user = authenticate(username=u_email, password=u_password)
            if user is not None:
                if user.check_password(u_password):
                     auth_login(request,user)
                     return redirect('/')
                else:
                     message = "Your username or password is incorrect."
                     form = LoginForm()
                     variables = RequestContext(request, {'form': form,'message':message})
                     return render_to_response('registration/login.html',variables)
            else:
                message = "Your username or password is incorrect."
                form = LoginForm()
                variables = RequestContext(request, {'form': form,'message':message})
                return render_to_response('registration/login.html',variables)

    else:
        request.session.modified = True
        form = LoginForm()
        variables = RequestContext(request, {'form': form})
        return render_to_response('registration/login.html',variables)


def register_success(request):
    return render_to_response('registration/register_success.html', RequestContext(request))

def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')


def register_page(request):

    if request.user.is_authenticated():
      return render_to_response('members/index.html', RequestContext(request))

    if request.method == 'POST':
      form = RegistrationForm(request.POST)

      if form.is_valid():
        user = DC801User.objects.create_user(
                  email         =    form.cleaned_data['email'],
                  password      =    form.cleaned_data['password1'],
                  handle        =    form.cleaned_data['handle'],
                  first_name    =    form.cleaned_data['first_name'],
                  last_name     =    form.cleaned_data['last_name'],
                  phone_number  =    form.cleaned_data['phone_number'],
        )
        return HttpResponseRedirect('/register/success/')

    else:
      form = RegistrationForm()

    variables = RequestContext(request, {
      'form': form
    })
    return render_to_response('registration/register.html', variables)

