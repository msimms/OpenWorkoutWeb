// -*- coding: utf-8 -*-
//
// MIT License
//
// Copyright (c) 2020 Mike Simms
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

/// @function power_training_zones
/// Returns the power training zones as a function of FTP.
function power_training_zones(ftp)
{
    // Dr. Andy Coggan 7 zone model
    // Zone 1 - Active Recovery - Less than 55% of FTP
    // Zone 2 - Endurance - 55% to 74% of FTP
    // Zone 3 - Tempo - 75% to 89% of FTP
    // Zone 4 - Lactate Threshold - 90% to 104% of FTP
    // Zone 5 - VO2 Max - 105% to 120% of FTP
    // Zone 6 - Anaerobic Capacity - More than 120% of FTP
    // Zone 6 is really anything over 120%,
    // Zone 7 is neuromuscular (i.e., shorts sprints at no specific power)
    zones = [];
    zones.push(ftp * 0.549);
    zones.push(ftp * 0.75);
    zones.push(ftp * 0.90);
    zones.push(ftp * 1.05);
    zones.push(ftp * 1.20);
    zones.push(ftp * 1.50);
    return zones;
}

/// @function compute_power_zone_distribution
/// Takes the list of power readings and determines how many belong in each power zone, based on the user's FTP.
function compute_power_zone_distribution(ftp, powers)
{
    let zones = power_training_zones(ftp);
    let distribution = Array.apply(null, Array(zones.length)).map(function (x, i) { return 0; });

    powers.forEach( datum => {
        let value = datum.value;
        let index = 0;
        let found = false;

        for (index = 0; index < zones.length; index++)
        {
            if (value <= zones[index])
            {
                distribution[index] = distribution[index] + 1;
                found = true;
                break;
            }
        }
    });
    return distribution;
}
