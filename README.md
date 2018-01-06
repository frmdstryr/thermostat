
# Thermostat

An open source thermostat using [enaml-native](https://codelv.com/projects/enaml-native/).

![thermostat](https://lh3.googleusercontent.com/AD1bQDZf5TvXZgo8XEdIdT9k12P8HFrPbSOet6vh8_wb3NSjArGxkWSE22VuLivJhPE=h310)

## Setup and usage

##### App

Download the [Thermostat](https://play.google.com/store/apps/details?id=com.codelv.thermostat) app from
the play store. I only have an Android app at the moment.


##### Hardware 

It also requires the arduino code be flashed onto a [particle photon](https://www.sparkfun.com/products/13774) 
board or [redbear duo](https://github.com/redbear/Duo/). I don't recommend the redbear duo as it's
wifi stability is poor and drops often (mtbf of ~8 hrs).

You will need a relay board like this [4 channel relay](https://www.amazon.com/JBtek-Channel-Module-Arduino-Raspberry/dp/B00KTEN3TM?SubscriptionId=AKIAILSHYYTFIVPWUY6Q&tag=duckduckgo-d-20&linkCode=xm2&camp=2025&creative=165953&creativeASIN=B00KTEN3TM)
or if you don't like clicking noises get a solid state one.
 
> Note: Solid state relays will NOT work with millivolt fireplaces!

And a DHT22, which you can get anywhere.

##### Case

If you want a case to mount on the wall. There's a 3d model that can be printed yourself or off of
3d hubs. Please [contact me](https://codelv.com/contact/) for it.


## License and Warranty

The code is GPL v3 and comes with no warranties whatsoever. I've been using this in my house
for about 2 years, it's not perfect but it works. Realize that connecting stuff to your 
furnace / hvac system can have serious implications if something goes wrong. Therefore: 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


## Donate

If you like this and want more projects like this please [donate](https://www.codelv.com/donate/).
 
 