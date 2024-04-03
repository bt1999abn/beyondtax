
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ServiceDummyApiView(APIView):
    def get(self, request, *args, **kwargs):
        data = {
            "header": {
                "img": "doc",
                "heading": "Udyam - MSME Registration",
                "paraBelowH": "Ready to give your business the recognition it deserves? With Udyam Registration, you open doors to growth, savings, and opportunities and with us, it's a breeze. Let’s get your business registered today!",
                "paraBBH": "Get Certificate starting from ₹500/-",
                "button": "Apply Now",
                "con1": {
                    "img": "whatsApp",
                    "details": "Text us on Whatsapp"
                },
                "con2": {
                    "img": "phone",
                    "details": "Schedule a Call"
                },
                "con3": {
                    "img": "headphone",
                    "details": "Call our Expert"
                }
            },
            "secondDiv": {
                "heading": "Udyam Registration: Your Business’s Official Stamp of Approval",
                "li1": "What is Udhyam",
                "li2": "Eligibility",
                "li3": "Checklist",
                "li4": "Essentials",
                "li5": "Benifits",
                "orangeheading": "What’s Udyam - MSME Registration?",
                "orangePara": "Udyam Registration is the government's official stamp of approval for your business. It recognizes you as a Micro, Small, or Medium Enterprise (MSME) and comes with a host of benefits.",
                "greenheading": "Who is Eligible to get Udyam - MSME Registration?",
                "greenheadingLi1": "Businesses involved in manufacturing or services.",
                "greenheadingLi2": "Companies that do not exceed the investment and turnover thresholds set for micro, small, or medium enterprises.",
                "redheading": "What are the documents required for Udyam Registration?",
                "aadharimg": "aadhar",
                "panImg": "pan",
                "bankImg": "bank",
                "renewalImg": "renewal",
                "addressImg": "address",
                "dueImg": "due",
                "govtFeeImg": "govtfee",
                "aadhar": "Aadhar",
                "pan": "PAN",
                "bankDetails": "Bank Details",
                "businessAddProof": "Business Assress Proof",
                "purpleheading": "What is the Due Date, Govt. Fee payable & Renewal Date fees for Udyam Registration?",
                "whiteInPurp": {
                    "boldDue": "Due Date",
                    "paraDue": "There is no specific due date for Udyam Registration. Businesses can apply for it at any time.",
                    "boldGov": "Govt. Fee",
                    "paraGov": "Udyam Registration is free of charge; government does not levy any fee for this registration.",
                    "boldRenew": "Renewal",
                    "renewPara": "Once and Done: No Renewals Needed Lifetime Validity – One-time process, no expiry date!"
                },
                "pinkheading": "What are the Benefits of Udyam Registration?",
                "pinkLoan": {
                    "heading": "Easy Bank Loans",
                    "des": "Think of it as a fast pass in the bank loan queue."
                },
                "pinkTax": {
                    "heading": "Fee & Tax Relief",
                    "des": "Pay less Govt. challan amount & tax, save more money!"
                },
                "pinkPriority": {
                    "heading": "Becomes Priority",
                    "des": "Get ahead of others when bidding for government tenders."
                }
            },
            "thirdDiv": {
                "heading": "The Step-by-Step Guide: How to Register for Udyam Registration",
                "img": "firstImg"
            },
            "serviceFaq": {
                "heading": "Frequently Asked Questions",
                "paraBelowH": "Find answers to common questions and concerns about our program.",
                "btn": "Contact Us",
                "difference": {
                    "ques": "What’s the difference between Udyog Aadhaar and Udyam Registration?",
                    "ans": "Udyog Aadhaar is the old system; Udyam Registration is the new and improved one.",
                    "img": "arUp"
                },
                "time": {
                    "ques": "How quickly can I get registered for Udyam Certificate?",
                    "ans": "If you're all set with your documents, it can be same-day fast!"
                },
                "img": "arDown",
                "noAadhar": {
                    "ques": "I don't have an Aadhaar card, now what?",
                    "ans": "You'll need to get one; it's an essential requirement."
                },
                "moreBuss": {
                    "ques": "What if I have more than one business?",
                    "ans": "Each business needs its own unique registration."
                },
                "editForm": {
                    "ques": "Made a mistake on the form, can I fix it?",
                    "ans": "Absolutely, with the edit feature, you can make corrections."
                }
            }
        }
        return JsonResponse(data)


class MobileNumberDummyApi(APIView):
    def post(self, request, *args, **kwargs):
        mobile_number = request.data.get('mobile_number')
        if mobile_number:
            otp = 1234

            return Response({"message": "otp sent successfully."})
        return Response({"Please Enter Your Mobile Number."}, status=400)


class VerifyOtpDummyApi(APIView):
    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp')
        if otp == '1234':
            return Response({'message': 'Otp Verification Successful'})
        return Response({'messgae': 'Please Enter Valid Otp.'}, status=400)
