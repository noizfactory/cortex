##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import glob
import unittest

import nuke

import IECore
import IECoreImage
import IECoreNuke

class SceneCacheReaderTest( IECoreNuke.TestCase ) :

	def setUp( self ) :
		nuke.scriptClear()

	def tearDown( self ) :
		nuke.scriptClear()
		for f in glob.glob( "test/IECoreNuke/scripts/data/sceneCacheTestResults*.exr" ) :
			try:
				os.remove(f)
			except:
				pass

	def testLoadedScriptWithRetime( self ) :

		nuke.scriptOpen("test/IECoreNuke/scripts/sceneCacheTest.nk" )
		w = nuke.toNode("Write1")
		frames = [ 1, 10, 20, 30, 40, 50, 60, 70, 80 ]
		nuke.executeMultiple( [ w ], [(f,f,1) for f in frames] )
		for f in frames :
			imageA = IECore.Reader.create( "test/IECoreNuke/scripts/data/sceneCacheExpectedResults.%04d.exr" % f )()
			imageB = IECore.Reader.create( "test/IECoreNuke/scripts/data/sceneCacheTestResults.%04d.exr" % f )()
			self.assertEqual( IECoreImage.ImageDiffOp()( imageA = imageA, imageB = imageB, maxError = 0.05 ).value, False )

		n = nuke.toNode("ieSceneCacheReader4")
		v = n.knob('sceneView')
		self.assertEqual( set(v.getSelectedItems()), set(['/root/A/a']) )

		# now force loading A+B and test in frame 20
		v.setSelectedItems(['/root/A/a', '/root/B/b', '/root/bezier1', '/root/particle1'])
		self.assertEqual( set(v.getSelectedItems()), set(['/root/A/a', '/root/B/b', '/root/bezier1', '/root/particle1' ]) )
		nuke.executeMultiple( [ w ], [(20,20,1)] )
		imageA = IECore.Reader.create( "test/IECoreNuke/scripts/data/sceneCacheExpectedResultsB.0020.exr" )()
		imageB = IECore.Reader.create( "test/IECoreNuke/scripts/data/sceneCacheTestResults.0020.exr" )()
		self.assertEqual( IECoreImage.ImageDiffOp()( imageA = imageA, imageB = imageB, maxError = 0.05 ).value, False )

	def testUVMapping( self ):

		nuke.scriptOpen("test/IECoreNuke/scripts/sceneCacheTestUV.nk" )
		w = nuke.toNode("Write1")
		frames = [ 1, 10, 20, 30, 40, 50 ]
		nuke.executeMultiple( [ w ], [(f,f,1) for f in frames] )
		for f in frames :
			imageA = IECore.Reader.create( "test/IECoreNuke/scripts/data/sceneCacheExpectedUVResults.%04d.exr" % f )()
			imageB = IECore.Reader.create( "test/IECoreNuke/scripts/data/sceneCacheTestResultsUV.%04d.exr" % f )()
			self.assertEqual( IECoreImage.ImageDiffOp()( imageA = imageA, imageB = imageB, maxError = 0.05 ).value, False )

	def testSelectionHash( self ):
		"""
		Test selection hash refresh when using motion blur
		"""
		for i in range( 10 ):
			constant = nuke.createNode( "Constant" )
			constant.knob( "color" ).setValue( 1 )
			constant.knob( "channels" ).setValue( "rgba" )

			reader = nuke.createNode( "ieSceneCacheReader" )
			reader.knob( "file" ).setValue( "test/IECoreNuke/scripts/animatedSpheres.scc" )
			reader.forceValidate()
			widget = reader.knob( "sceneView" )
			widget.setSelectedItems( ["/root/A/a"] )

			camera = nuke.createNode( "Camera2")
			camera.knob( "translate" ).setValue( [0,0,12] )
			render = nuke.createNode( "ScanlineRender" )

			render.setInput( 0, camera )
			render.setInput( 1, reader )
			render.setInput( 2, constant )
			render.knob( "samples" ).setValue( 2 )

			writer = nuke.createNode( "Write" )
			writer.knob( "file" ).setValue( "test/IECoreNuke/scripts/data/sceneCacheTestResultsSelectionHash.####.exr" )
			writer.setInput( 0, render )
			writer.knob( "file_type" ).setValue( "exr" )
			nuke.execute( writer, 1, 2, 1 )

			widget = reader.knob( "sceneView" )
			widget.setSelectedItems( ["/root/A/a"] )
			opHashes = reader.opHashes()
			widget.setSelectedItems( ["/root/B/b"] )
			diffOpHashes = reader.opHashes()

			self.assertNotEqual( opHashes, diffOpHashes )

if __name__ == "__main__":
	unittest.main()

