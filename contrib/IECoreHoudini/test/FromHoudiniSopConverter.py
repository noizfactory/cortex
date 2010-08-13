##########################################################################
#
#  Copyright 2010 Dr D Studios Pty Limited (ACN 127 184 954) (Dr. D Studios),
#  its affiliates and/or its licensors.
#
#  Copyright (c) 2010, Image Engine Design Inc. All rights reserved.
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

import hou
import IECore
import IECoreHoudini
import unittest
import os

class TestFromHoudiniSopConverter( unittest.TestCase ):

	def createBox(self):
		obj = hou.node("/obj")
		geo = obj.createNode("geo", run_init_scripts=False)
		box = geo.createNode( "box" )
		return box

	def createTorus(self):
		obj = hou.node("/obj")
		geo = obj.createNode("geo", run_init_scripts=False)
		torus = geo.createNode( "torus" )
		return torus

	def createPoints(self):
		obj = hou.node("/obj")
		geo = obj.createNode("geo", run_init_scripts=False)
		box = geo.createNode( "box" )
		facet = geo.createNode( "facet" )
		facet.parm("postnml").set(True)
		points = geo.createNode( "scatter" )
		facet.setInput( 0, box )
		points.setInput( 0, facet )
		return points

	# creates a converter
	def testCreateConverter(self):
		box = self.createBox()
		converter = IECoreHoudini.FromHoudiniSopConverter( box )
		assert( converter )
		return converter

	# creates a converter
	def testFactory( self ) :
		box = self.createBox()
		converter = IECoreHoudini.FromHoudiniSopConverter.create( box )
		self.assert_( converter.isInstanceOf( IECore.TypeId( IECoreHoudini.TypeId.FromHoudiniSopConverter ) ) )
		converter = IECoreHoudini.FromHoudiniNodeConverter.create( box )
		self.assert_( converter.isInstanceOf( IECore.TypeId( IECoreHoudini.TypeId.FromHoudiniSopConverter ) ) )
		converter = IECoreHoudini.FromHoudiniNodeConverter.create( box, IECore.TypeId.Primitive )
		self.assert_( converter.isInstanceOf( IECore.TypeId( IECoreHoudini.TypeId.FromHoudiniSopConverter ) ) )
		converter = IECoreHoudini.FromHoudiniNodeConverter.create( box, IECore.TypeId.Group )
		self.assertEqual( converter, None )

	# performs geometry conversion
	def testDoConversion(self):
		converter = self.testCreateConverter()
		result = converter.convert()
		assert( result != None )

	# convert a mesh
	def testConvertMesh(self):
		torus = self.createTorus()
		converter = IECoreHoudini.FromHoudiniSopConverter( torus )
		result = converter.convert()
		assert( result.typeId() == IECore.MeshPrimitive.staticTypeId() )
		bbox = result.bound()
		assert( bbox.min.x == -1.5 )
		assert( bbox.max.x == 1.5 )
		assert( result.numFaces()==100 )
		assert( len( result.verticesPerFace ), 100 )
		for i in range( len( result.verticesPerFace ) ):
			assert( result.verticesPerFace[i]==4 )
		assert( len( result.vertexIds )==400 )
		for i in range( len( result.vertexIds ) ):
			assert( result.vertexIds[i]>=0 )
			assert( result.vertexIds[i]<100 )

	# test prim/vertex attributes
	def testConvertPrimVertAttributes(self):
		torus = self.createTorus()
		geo = torus.parent()

		# add vertex normals
		facet = geo.createNode( "facet", node_name = "add_point_normals" )
		facet.parm("postnml").set(True)
		facet.setInput( 0, torus )

		# add a primitive colour attributes
		primcol = geo.createNode( "primitive", node_name = "prim_colour" )
		primcol.parm("doclr").set(1)
		primcol.parm("diffr").setExpression("rand($PR)")
		primcol.parm("diffg").setExpression("rand($PR+1)")
		primcol.parm("diffb").setExpression("rand($PR+2)")
		primcol.setInput( 0, facet )

		# add a load of different vertex attributes
		vert_f1 = geo.createNode( "attribcreate", node_name = "vert_f1" )
		vert_f1.parm("name").set("vert_f1")
		vert_f1.parm("class").set(3)
		vert_f1.parm("value1").setExpression("$VTX*0.1")
		vert_f1.setInput( 0, primcol )

		vert_f2 = geo.createNode( "attribcreate", node_name = "vert_f2" )
		vert_f2.parm("name").set("vert_f2")
		vert_f2.parm("class").set(3)
		vert_f2.parm("size").set(2)
		vert_f2.parm("value1").setExpression("$VTX*0.1")
		vert_f2.parm("value2").setExpression("$VTX*0.1")
		vert_f2.setInput( 0, vert_f1 )

		vert_f3 = geo.createNode( "attribcreate", node_name = "vert_f3" )
		vert_f3.parm("name").set("vert_f3")
		vert_f3.parm("class").set(3)
		vert_f3.parm("size").set(3)
		vert_f3.parm("value1").setExpression("$VTX*0.1")
		vert_f3.parm("value2").setExpression("$VTX*0.1")
		vert_f3.parm("value3").setExpression("$VTX*0.1")
		vert_f3.setInput( 0, vert_f2 )

		vert_i1 = geo.createNode( "attribcreate", node_name = "vert_i1" )
		vert_i1.parm("name").set("vert_i1")
		vert_i1.parm("class").set(3)
		vert_i1.parm("type").set(1)
		vert_i1.parm("value1").setExpression("$VTX*0.1")
		vert_i1.setInput( 0, vert_f3 )

		vert_i2 = geo.createNode( "attribcreate", node_name = "vert_i2" )
		vert_i2.parm("name").set("vert_i2")
		vert_i2.parm("class").set(3)
		vert_i2.parm("type").set(1)
		vert_i2.parm("size").set(2)
		vert_i2.parm("value1").setExpression("$VTX*0.1")
		vert_i2.parm("value2").setExpression("$VTX*0.1")
		vert_i2.setInput( 0, vert_i1 )

		vert_i3 = geo.createNode( "attribcreate", node_name = "vert_i3" )
		vert_i3.parm("name").set("vert_i3")
		vert_i3.parm("class").set(3)
		vert_i3.parm("type").set(1)
		vert_i3.parm("size").set(3)
		vert_i3.parm("value1").setExpression("$VTX*0.1")
		vert_i3.parm("value2").setExpression("$VTX*0.1")
		vert_i3.parm("value3").setExpression("$VTX*0.1")
		vert_i3.setInput( 0, vert_i2 )

		vert_v3f = geo.createNode( "attribcreate", node_name = "vert_v3f" )
		vert_v3f.parm("name").set("vert_v3f")
		vert_v3f.parm("class").set(3)
		vert_v3f.parm("type").set(2)
		vert_v3f.parm("value1").setExpression("$VTX*0.1")
		vert_v3f.parm("value2").setExpression("$VTX*0.1")
		vert_v3f.parm("value3").setExpression("$VTX*0.1")
		vert_v3f.setInput( 0, vert_i3 )

		detail_i3 = geo.createNode( "attribcreate", node_name = "detail_i3" )
		detail_i3.parm("name").set("detail_i3")
		detail_i3.parm("class").set(0)
		detail_i3.parm("type").set(1)
		detail_i3.parm("size").set(3)
		detail_i3.parm("value1").set(123)
		detail_i3.parm("value2").set(456.789) # can we catch it out with a float?
		detail_i3.parm("value3").set(789)
		detail_i3.setInput( 0, vert_v3f )

		out = geo.createNode( "null", node_name="OUT" )
		out.setInput( 0, detail_i3 )

		# convert it all
		converter = IECoreHoudini.FromHoudiniSopConverter( out )
		assert( converter )
		result = converter.convert()
		assert( result.typeId() == IECore.MeshPrimitive.staticTypeId() )
		bbox = result.bound()
		assert( bbox.min.x == -1.5 )
		assert( bbox.max.x == 1.5 )
		assert( result.numFaces()==100 )
		assert( len( result.verticesPerFace ), 100 )
		for i in range( len( result.verticesPerFace ) ):
			assert( result.verticesPerFace[i]==4 )
		assert( len( result.vertexIds )==400 )
		for i in range( len( result.vertexIds ) ):
			assert( result.vertexIds[i]>=0 )
			assert( result.vertexIds[i]<100 )

		# test point attributes
		assert( "P" in result )
		assert( result['P'].data.typeId() == IECore.TypeId.V3fVectorData )
		assert( result['P'].interpolation == IECore.PrimitiveVariable.Interpolation.Vertex )
		assert( result['P'].data.size()==100 )
		assert( "N" in result )
		assert( result['N'].data.typeId() == IECore.TypeId.V3fVectorData )
		assert( result['N'].interpolation == IECore.PrimitiveVariable.Interpolation.Varying )
		assert( result['N'].data.size()==100 )

		# test detail attributes
		assert( "detail_i3" in result )
		assert( result['detail_i3'].data.typeId() == IECore.TypeId.V3iVectorData )
		assert( result['detail_i3'].interpolation == IECore.PrimitiveVariable.Interpolation.Constant )
		assert( result['detail_i3'].data.size()==1 )
		assert( result['detail_i3'].data[0].x == 123 )
		assert( result['detail_i3'].data[0].y == 456 )
		assert( result['detail_i3'].data[0].z == 789 )

		# test primitive attributes
		assert( "Cd" in result )
		assert( result["Cd"].data.typeId() == IECore.TypeId.V3fVectorData )
		assert( result["Cd"].interpolation == IECore.PrimitiveVariable.Interpolation.Uniform )
		assert( result["Cd"].data.size() == 100 )
		for i in range(100):
			for j in range(3):
				assert( result["Cd"].data[i][j]>=0.0 )
				assert( result["Cd"].data[i][j]<=1.0 )

		# test vertex attributes
		attrs = [ "vert_f1", "vert_f2", "vert_f3", "vert_i1", "vert_i2", "vert_i3", "vert_v3f" ]
		for a in attrs:
			assert( a in result )
			assert( result[a].interpolation == IECore.PrimitiveVariable.Interpolation.FaceVarying )
			assert( result[a].data.size()== 400 )
		assert( result["vert_f1"].data.typeId() == IECore.FloatVectorData.staticTypeId() )
		assert( result["vert_f2"].data.typeId() == IECore.V2fVectorData.staticTypeId() )
		assert( result["vert_f3"].data.typeId() == IECore.V3fVectorData.staticTypeId() )
		for i in range(400):
			for j in range(3):
				assert( result["vert_f3"].data[i][j] >= 0.0 )
				assert( result["vert_f3"].data[i][j] < 0.4 )
		assert( result["vert_i1"].data.typeId() == IECore.IntVectorData.staticTypeId() )
		assert( result["vert_i2"].data.typeId() == IECore.V2iVectorData.staticTypeId() )
		assert( result["vert_i3"].data.typeId() == IECore.V3iVectorData.staticTypeId() )
		for i in range(400):
			for j in range(3):
				assert( result["vert_i3"].data[i][j] == 0 )
		assert( result["vert_v3f"].data.typeId() == IECore.V3fVectorData.staticTypeId() )


	# convert some points
	def testConvertPoints(self):
		points = self.createPoints()
		converter = IECoreHoudini.FromHoudiniSopConverter( points )
		result = converter.convert()
		assert( result.typeId() == IECore.PointsPrimitive.staticTypeId() )
		assert( points.parm('npts').eval() == result.numPoints )
		assert( "P" in result.keys() )
		assert( "N" in result.keys() )

	# simple attribute conversion
	def testSetupAttributes(self):
		points = self.createPoints()
		geo = points.parent()
		attr = geo.createNode( "attribcreate" )
		attr.setInput( 0, points )
		attr.parm("name").set( "test_attribute" )
		attr.parm("type").set(0) # float
		attr.parm("size").set(1) # 1 element
		attr.parm("value1").set(123.456)
		attr.parm("value2").set(654.321)
		converter = IECoreHoudini.FromHoudiniSopConverter( attr )
		result = converter.convert()
		assert( "test_attribute" in result.keys() )
		assert( result["test_attribute"].data.size() == points.parm('npts').eval() )
		return attr

	# testing point attributes and types
	def testPointAttributes(self):
		attr = self.testSetupAttributes()
		converter = IECoreHoudini.FromHoudiniSopConverter( attr )
		result = converter.convert()
		attr.parm("value1").set(123.456)
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.FloatVectorData )
		assert( result["test_attribute"].data[0] > 123.0 )
		assert( result["test_attribute"].data.size() == 5000 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Varying )
		attr.parm("type").set(1) # integer
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.IntVectorData )
		assert( result["test_attribute"].data[0] == 123 )
		assert( result["test_attribute"].data.size() == 5000 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Varying )
		attr.parm("type").set(0) # float
		attr.parm("size").set(2) # 2 elementS
		attr.parm("value2").set(456.789)
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V2fVectorData )
		assert( result["test_attribute"].data[0] == IECore.V2f( 123.456, 456.789 ) )
		assert( result["test_attribute"].data.size() == 5000 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Varying )
		attr.parm("type").set(1) # int
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V2iVectorData )
		assert( result["test_attribute"].data[0] == IECore.V2i( 123, 456 ) )
		assert( result["test_attribute"].data.size() == 5000 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Varying )
		attr.parm("type").set(0) # float
		attr.parm("size").set(3) # 3 elements
		attr.parm("value3").set(999.999)
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V3fVectorData )
		assert( result["test_attribute"].data[0] == IECore.V3f( 123.456, 456.789, 999.999 ) )
		assert( result["test_attribute"].data.size() == 5000 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Varying )
		attr.parm("type").set(1) # int
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V3iVectorData )
		assert( result["test_attribute"].data[0] == IECore.V3i( 123, 456, 999 ) )
		assert( result["test_attribute"].data.size() == 5000 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Varying )

	# testing detail attributes and types
	def testDetailAttributes(self):
		attr = self.testSetupAttributes()
		attr.parm("class").set(0) # detail attribute
		converter = IECoreHoudini.FromHoudiniSopConverter( attr )
		result = converter.convert()
		attr.parm("value1").set(123.456)
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.FloatVectorData )
		assert( result["test_attribute"].data[0] > 123.0 )
		assert( result["test_attribute"].data.size() == 1 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Constant )
		attr.parm("type").set(1) # integer
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.IntVectorData )
		assert( result["test_attribute"].data[0] == 123 )
		assert( result["test_attribute"].data.size() == 1 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Constant )
		attr.parm("type").set(0) # float
		attr.parm("size").set(2) # 2 elementS
		attr.parm("value2").set(456.789)
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V2fVectorData )
		assert( result["test_attribute"].data[0] == IECore.V2f( 123.456, 456.789 ) )
		assert( result["test_attribute"].data.size() == 1 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Constant )
		attr.parm("type").set(1) # int
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V2iVectorData )
		assert( result["test_attribute"].data[0] == IECore.V2i( 123, 456 ) )
		assert( result["test_attribute"].data.size() == 1 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Constant )
		attr.parm("type").set(0) # float
		attr.parm("size").set(3) # 3 elements
		attr.parm("value3").set(999.999)
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V3fVectorData )
		assert( result["test_attribute"].data[0] == IECore.V3f( 123.456, 456.789, 999.999 ) )
		assert( result["test_attribute"].data.size() == 1 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Constant )
		attr.parm("type").set(1) # int
		result = converter.convert()
		assert( result["test_attribute"].data.typeId() == IECore.TypeId.V3iVectorData )
		assert( result["test_attribute"].data[0] == IECore.V3i( 123, 456, 999 ) )
		assert( result["test_attribute"].data.size() == 1 )
		assert( result["test_attribute"].interpolation == IECore.PrimitiveVariable.Interpolation.Constant )

	# testing that float[4] doesn't work!
	def testFloat4attr(self): # we can't deal with float 4's right now
		attr = self.testSetupAttributes()
		attr.parm("name").set( "test_attribute" )
		attr.parm("size").set(4) # 4 elements per point-attribute
		converter = IECoreHoudini.FromHoudiniSopConverter( attr )
		result = converter.convert()
		assert( "test_attribute" not in result.keys() ) # invalid due to being float[4]

	# testing conversion of animating geometry
	def testAnimatingGeometry(self):
		obj = hou.node("/obj")
		geo = obj.createNode("geo", run_init_scripts=False)
		torus = geo.createNode( "torus" )
		facet = geo.createNode( "facet" )
		facet.parm("postnml").set(True)
		mountain = geo.createNode( "mountain" )
		mountain.parm("offset1").setExpression( "$FF" )
		points = geo.createNode( "scatter" )
		facet.setInput( 0, torus )
		mountain.setInput( 0, facet )
		points.setInput( 0, mountain )
		converter = IECoreHoudini.FromHoudiniSopConverter( points )
		hou.setFrame(1)
		points_1 = converter.convert()
		hou.setFrame(2)
		points_2 = converter.convert()
		assert( points_1["P"].data != points_2["P"].data )

	# testing we can handle an object being deleted
	def testObjectWasDeleted(self):
		obj = hou.node("/obj")
		geo = obj.createNode("geo", run_init_scripts=False)
		torus = geo.createNode( "torus" )
		converter = IECoreHoudini.FromHoudiniSopConverter( torus )
		g1 = converter.convert()
		torus.destroy()
		g2 = converter.convert()
		assert( g2==None )
	
	# testing converting a Houdini particle primitive with detail and point attribs
	def testParticlePrimitive( self ) :
		obj = hou.node("/obj")
		geo = obj.createNode( "geo", run_init_scripts=False )
		popnet = geo.createNode( "popnet" )
		location = popnet.createNode( "location" )
		detailAttr = popnet.createOutputNode( "attribcreate" )
		detailAttr.parm("name").set( "float3detail" )
		detailAttr.parm("class").set( 0 ) # detail
		detailAttr.parm("type").set( 0 ) # float
		detailAttr.parm("size").set( 3 ) # 3 elements
		detailAttr.parm("value1").set( 1 )
		detailAttr.parm("value2").set( 2 )
		detailAttr.parm("value3").set( 3 )
		pointAttr = detailAttr.createOutputNode( "attribcreate" )
		pointAttr.parm("name").set( "float3point" )
		pointAttr.parm("class").set( 2 ) # point
		pointAttr.parm("type").set( 0 ) # float
		pointAttr.parm("size").set( 3 ) # 3 elements
		pointAttr.parm("value1").set( 1 )
		pointAttr.parm("value2").set( 2 )
		pointAttr.parm("value3").set( 3 )
		
		hou.setFrame( 5 )
		converter = IECoreHoudini.FromHoudiniSopConverter( pointAttr )
		points = converter.convert()
		
		self.assertEqual( type(points), IECore.PointsPrimitive )
		self.assertEqual( points.variableSize( IECore.PrimitiveVariable.Interpolation.Vertex ), 21 )
		self.assertEqual( points["float3detail"].interpolation, IECore.PrimitiveVariable.Interpolation.Constant )
		self.assertEqual( type(points["float3detail"].data), IECore.V3fData )
		self.assert_( points["float3detail"].data.equalWithRelError( IECore.V3f( 1, 2, 3 ), 1e-10 ) )
		self.assertEqual( type(points["float3point"].data), IECore.V3fVectorData )
		self.assertEqual( points["float3point"].interpolation, IECore.PrimitiveVariable.Interpolation.Vertex )
		for p in points["float3point"].data :
			self.assert_( p.equalWithRelError( IECore.V3f( 1, 2, 3 ), 1e-10 ) )
		
		add = pointAttr.createOutputNode( "add" )
		add.parm( "keep" ).set( 1 ) # deletes primitive and leaves points
		
		converter = IECoreHoudini.FromHoudiniSopConverter( add )
		points2 = converter.convert()
		
		self.assertEqual( points2, points )
	
	def setUp( self ) :
                os.environ["IECORE_PROCEDURAL_PATHS"] = "test/procedurals"

	def tearDown( self ) :
                pass

if __name__ == "__main__":
    unittest.main()
