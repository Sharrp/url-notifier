//
//  NSData+NSData_Conversion.m
//  url-notifier
//
//  Created by Anton Furin on 3/16/14.
//  Copyright (c) 2014 Anton Furin. All rights reserved.
//

#import "NSData+NSData_Conversion.h"

@implementation NSData (NSData_Conversion)

/* Returns hexadecimal string of NSData. Empty string if data is empty.   */
- (NSString *)hexadecimalString
{
    const unsigned char *dataBuffer = (const unsigned char *)[self bytes];
    if (!dataBuffer)
    {
        return [NSString string];
    }
    
    NSUInteger          dataLength  = [self length];
    NSMutableString     *hexString  = [NSMutableString stringWithCapacity:(dataLength * 2)];
    for (int i = 0; i < dataLength; ++i)
        [hexString appendString:[NSString stringWithFormat:@"%02lx", (unsigned long)dataBuffer[i]]];

    return [NSString stringWithString:hexString];
}

@end
