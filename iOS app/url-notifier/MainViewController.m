//
//  MainViewController.m
//  url-notifier
//
//  Created by Anton Furin on 2/28/14.
//  Copyright (c) 2014 Anton Furin. All rights reserved.
//

#import "MainViewController.h"

#import "NSData+NSData_Conversion.h"

@interface MainViewController ()

@end

@implementation MainViewController

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self)
    {
        self.udid = (NSString *)[[NSUserDefaults standardUserDefaults] objectForKey:@"udid"];
    }
    return self;
}

- (void)viewDidLoad
{
    [super viewDidLoad];
    
    [self checkPushAvailability];
    
    if (self.urlStringToOpen != nil)
    {
        [self openURL:self.urlStringToOpen];
    }
}

- (void) checkPushAvailability
{
    UIRemoteNotificationType status = [[UIApplication sharedApplication] enabledRemoteNotificationTypes];
    if (status == UIRemoteNotificationTypeNone)
    {
        [self hideAll];
        self.udidStatusLabel.text = @"Push notifications is not available";
        self.contextHelpLabel.hidden = NO;
        self.contextHelpLabel.text = @"You should allow push notifications for this app in phone settings";
    }
    else if (self.udid)
    {
        [self hideAll];
        self.udidStatusLabel.text = @"Your device ID is";
        self.udidLabel.text = self.udid;
        self.udidLabel.hidden = NO;
        self.contextHelpLabel.hidden = NO;
        self.contextHelpLabel.text = @"Add it to your desktop client and start pushing!";
    }
}


#pragma mark -- Device id management

- (void) tokenUpdated
{
    [self requestUdidOrUpdateToken];
}

- (void) tokenUpdateFailed
{
    [self hideAll];
    self.udidStatusLabel.text = @"That sad moment, when you have to relaunch application";
}

- (void) requestUdidOrUpdateToken
{
    [self hideAll];
    self.udidStatusLabel.text = @"Getting device id";
    [self.udidActivityIndicator startAnimating];
    
    NSString *did = [[[UIDevice currentDevice] identifierForVendor] UUIDString];
    NSData *deviceToken = (NSData *)[[NSUserDefaults standardUserDefaults] objectForKey:@"last_token"];
    NSString *strToken = [deviceToken hexadecimalString];
    NSString* jsonData = [NSString stringWithFormat:@"{\"did\":\"%@\", \"token\":\"%@\"}", did, strToken];
    
    // Send token to server
    NSURL *requestURL = [NSURL URLWithString:@"http://188.226.174.130:5000/device/"];
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:requestURL];
    request.HTTPMethod = @"POST";
    [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    request.HTTPBody = [jsonData dataUsingEncoding:NSUTF8StringEncoding];
    
    NSOperationQueue *queue = [[NSOperationQueue alloc] init];
    [NSURLConnection sendAsynchronousRequest:request
                                       queue:queue
                           completionHandler:^(NSURLResponse* response, NSData* data, NSError* error){
                               if ([data length] > 0 && error == nil)
                               {
                                   NSString *udid = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
                                   NSLog(@"Received udid: %@", udid);
                                   self.udidStatusLabel.text = @"Your device ID is";
                                   self.udidLabel.text = udid;
                                   self.udidLabel.hidden = NO;
                                   
                                   [[NSUserDefaults standardUserDefaults] setObject:udid forKey:@"udid"];
                                   [[NSUserDefaults standardUserDefaults] setObject:deviceToken forKey:@"last_token"];
                                   [[NSUserDefaults standardUserDefaults] synchronize];
                               }
                               else
                               {
                                   self.udidStatusLabel.text = @"Can't get device id";
                                   self.getIdButton.hidden = NO;
                                   NSLog(@"Error on sending token: %@", error);
                               }
                               
                               [self.udidActivityIndicator stopAnimating];
                           }];
}

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
}


#pragma mark -- Public methods 

- (void) openURL:(NSString *)urlString
{
    // Allowed characters should not be escaped
    NSRange lcEnglishRange;
    lcEnglishRange.location = (unsigned int)'a';
    lcEnglishRange.length = 26;
    NSMutableCharacterSet *allowed = [NSCharacterSet characterSetWithRange:lcEnglishRange];
    lcEnglishRange.location = (unsigned int)'A';
    lcEnglishRange.length = 26;
    [allowed addCharactersInRange:lcEnglishRange];
    [allowed formUnionWithCharacterSet:[NSCharacterSet decimalDigitCharacterSet]];
    [allowed addCharactersInString:@"%!*'();:@&=+$,/?#[].-"];

    NSString *escapedUrl = [urlString stringByAddingPercentEncodingWithAllowedCharacters:allowed];
    NSURL *url = [NSURL URLWithString:escapedUrl];
//    NSLog(@"URL: %@", urlString);
//    NSLog(@"Escaped: %@", escapedUrl);
//    NSLog(@"NSURL: %@", url);
    
    NSString *status = [NSString stringWithFormat:@"Opening: %@", [url host]];
    self.contextHelpLabel.text = status;
    self.contextHelpLabel.hidden = NO;
    dispatch_async(dispatch_get_main_queue(), ^{
        if (![[UIApplication sharedApplication] openURL:url])
        {
            NSLog(@"Failed to open url: %@\n", url);
            self.contextHelpLabel.text = [NSString stringWithFormat:@"Failed to open url: %@", url];
        }
    });
}

- (void) requestLastUrl
{
    NSString *did = [[[UIDevice currentDevice] identifierForVendor] UUIDString];
    NSString* jsonData = [NSString stringWithFormat:@"{\"did\":\"%@\"}", did];
    
    // Request last pushed url from the server
    NSURL *requestURL = [NSURL URLWithString:@"http://188.226.174.130:5000/lasturl/"];
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:requestURL];
    request.HTTPMethod = @"POST";
    [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    request.HTTPBody = [jsonData dataUsingEncoding:NSUTF8StringEncoding];
    
    NSOperationQueue *queue = [[NSOperationQueue alloc] init];
    void (^lastUrlReceived)(NSURLResponse*, NSData*, NSError*) = ^(NSURLResponse* response, NSData* data, NSError* error) {
        if ([data length] > 0 && error == nil)
        {
            NSDictionary *dataDic = [NSJSONSerialization JSONObjectWithData:data
                                                                    options:NSJSONReadingAllowFragments error:nil];
            if (!dataDic)
            {
                NSString *dataString = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
                NSLog(@"requestLastUrl: Incorrect data received: %@", dataString);
            }
            else
            {
                if (dataDic[@"url"])
                {
                    [self openURL:dataDic[@"url"]];
                }
                else
                {
                    NSLog(@"%@", @"There is no url for this device on the server");
                }
            }
        }
        else
        {
            NSLog(@"Error on receiving last url: %@", error);
        }
    };
    [NSURLConnection sendAsynchronousRequest:request queue:queue
                           completionHandler:lastUrlReceived];
}


#pragma mark -- UI methods

- (IBAction) helpButtonTap
{
    NSString *urlString = @"https://github.com/Sharrp/url-notifier/blob/master/README.md";
    [self openURL:urlString];
}

- (IBAction) tryToGetDeviceId
{
    [self requestUdidOrUpdateToken];
}

- (void) hideAll
{
    self.udidLabel.hidden = YES;
    self.getIdButton.hidden = YES;
    self.contextHelpLabel.hidden = YES;
}

- (void) enterForeground
{
    self.contextHelpLabel.hidden = YES;
    [self checkPushAvailability];
}

- (UIStatusBarStyle)preferredStatusBarStyle
{
    return UIStatusBarStyleLightContent;
}

@end
