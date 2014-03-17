//
//  MainViewController.m
//  url-notifier
//
//  Created by Anton Furin on 2/28/14.
//  Copyright (c) 2014 Anton Furin. All rights reserved.
//

#import "MainViewController.h"

@interface MainViewController ()

@end

@implementation MainViewController

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        // Custom initialization
    }
    return self;
}

- (void)viewDidLoad
{
    [super viewDidLoad];
    
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(udidUpdated)
                                                 name:@"udid update" object:nil];
    [self udidUpdated];
    
    if (self.urlToOpen != nil)
    {
        [self openURL:self.urlToOpen];
    }
}

- (void) udidUpdated
{
    NSString *new_udid = (NSString *)[[NSUserDefaults standardUserDefaults] objectForKey:@"udid"];
    if (new_udid)
    {
        self.udid = new_udid;
        [self updateStatus:[NSString stringWithFormat:@"Your udid is: %@", self.udid]];
    }
    else
    {
        [self updateStatus:@"Udid not received yet"];
    }
}

- (void) updateStatus:(NSString *)text
{
    self.statusLabel.text = text;
}

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Dispose of any resources that can be recreated.
}


#pragma mark -- Public methods 

- (void) openURL:(NSURL *)url
{
    if (![[UIApplication sharedApplication] openURL:url])
    {
        NSLog(@"Failed to open url: %@\n", url);
        [self updateStatus:[NSString stringWithFormat:@"Failed to open url: %@", url]];
    }
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
                NSURL *url = [NSURL URLWithString:dataDic[@"url"]];
                if (url)
                {
                    [self openURL:url];
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

@end
