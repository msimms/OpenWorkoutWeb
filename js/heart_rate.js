// -*- coding: utf-8 -*-
//
// MIT License
//
// Copyright (c) 2022 Michael J Simms
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

/// @function heart_rate_training_zones
/// Returns the heart rate training zones as a function of max heart rate.
function heart_rate_training_zones(resting_hr, max_hr) {
    let zones = [];

    // If given resting and max heart rates, use the Karvonen formula for determining zones based on hr reserve.
    if (resting_hr !== undefined) {
        zones.push(((max_hr - resting_hr) * .60) + resting_hr);
        zones.push(((max_hr - resting_hr) * .70) + resting_hr);
        zones.push(((max_hr - resting_hr) * .80) + resting_hr);
        zones.push(((max_hr - resting_hr) * .90) + resting_hr);
        zones.push(max_hr);
    }
    else {
        zones.push(max_hr * 0.60);
        zones.push(max_hr * 0.70);
        zones.push(max_hr * 0.80);
        zones.push(max_hr * 0.90);
    }
    return zones;
}

/// @function compute_heart_rate_zone_distribution
/// Takes the list of heart rate readings and determines how many belong in each training zone, based on the user's maximum heart rate.
function compute_heart_rate_zone_distribution(resting_hr, max_hr, hr_readings) {
    let zones = heart_rate_training_zones(resting_hr, max_hr);
    let distribution = Array.apply(null, Array(zones.length)).map(function (x, i) { return 0; })

    hr_readings.forEach( datum => {
        let value = datum.value;
        let index = 0;
        let found = false;

        for (index = 0; index < zones.length; index++) {
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
