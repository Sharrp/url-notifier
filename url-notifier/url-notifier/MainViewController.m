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
        self.statusLabel.text = [NSString stringWithFormat:@"Your udid is: %@", self.udid];
    }
    else
    {
        self.statusLabel.text = @"Udid not received yet";
    }
}

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Dispose of any resources that can be recreated.
}

- (void) openURL:(NSURL *)url
{
    if (![[UIApplication sharedApplication] openURL:url])
    {
        NSLog(@"Failed to open url: %@\n", url);
    }
}

@end
